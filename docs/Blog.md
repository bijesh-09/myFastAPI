# Blog: From a 19-hour FastAPI course to AWS CI/CD

Oct 14, 2026 · [@bijesh-09](https://github.com/bijesh-09)

I sat down with a free 19-hour FastAPI course and came out knowing far more than how to build an API: how to write tests that catch real bugs, how to ship a Docker image from a GitHub Action, and how to make a throwaway VM log into an AWS server by itself.

## I wanted to learn FastAPI. I got a lot more.

I thought I'd follow a long YouTube course, build a REST API, and call it a day. I did build the API. But I also ended up writing a test suite, setting up a CI/CD pipeline, and deploying to AWS in a way the course never showed me.

This post is the story: what I built, what broke, and the one part that almost made me quit (spoiler: it involves SSH keys). If you're staring at a huge tutorial and wondering whether it's worth the hours, hear me out.

If you only want the how-to, skip the story and open the EC2 deploy guide in the repo.

## What I built, and who taught me

A big shoutout first: the course is [freeCodeCamp's FastAPI course by Sanjeev](https://youtu.be/0sOvCWFmrtA), and it's free. Thank you both for being generous with your time.

The project is a posts-and-votes API. Users register and log in with a JWT, create, update and delete only their own posts, and vote on posts. It has query parameters for limit, skip and search, Alembic migrations, and a pytest suite. You can poke at the live version at https://my-fast-api-latest.onrender.com/docs (give it about 50 seconds to wake up, it's on Render's free tier).

The course deploys to Heroku and to an Ubuntu VM on DigitalOcean. I took a different road: Render, then AWS EC2, then a full CI/CD pipeline into EC2 with Docker Compose. That's where most of this story happens.

## Testing was harder than building the API

Here's what nobody warned me about: testing took me longer than writing the API. Just testing all the routes took more than 8 hours. For every route you have to think up the scenarios: the happy path, auth (no token, a garbage token, a token for a user that doesn't exist), not found, schema validation, and boundaries.

I learned a lot doing it:

- Fixtures, and the rule that pytest builds each fixture once per test and shares it, so there's only one client per test.
- `parametrize`, which turns ten copy-pasted tests into one.
- A separate test database that is dropped and rebuilt with Alembic for every test, so tests never depend on each other.
- Overriding the `get_db` dependency, and the trailing-slash trap where `/users` redirects to `/users/` with a 307.

It was honestly fun, even though it wore me out. And it paid off: my tests found real problems that I would never have noticed by clicking around in Swagger.

## The deployment ladder

I deliberately tried several ways to deploy, each one a little harder than the last, just to feel what's going on underneath.

**1. Render (the easy rung).** Create a web service and a Postgres instance, set your env vars, done. A few clicks. I used it two ways: sync it with the GitHub repo (deploy on every commit, or "after CI checks pass" once you have a pipeline), or point it at a Docker Hub image and trigger a deploy hook from CI after the image is pushed. Render fetches the new image by itself.

**2. EC2, fully by hand.** SSH in, `git clone`, `git pull origin main` after every push, install PostgreSQL, edit `pg_hba.conf` and `postgresql.conf`, write a systemd service for Postgres and another for gunicorn with a few workers, and enable them so they survive a reboot. It was painfully slow. But this is how things worked before containers, and under the hood it's still how the nicer platforms run your app.

**3. EC2 with Docker Compose.** I built the image locally, pushed it to Docker Hub, pulled the repo and the image on the server, and wrote a systemd service that runs `docker compose up` on boot. The hard part was writing the YAML. I ended up with a `docker-compose-dev.yml` for local testing and a `docker-compose-prod.yml`, because dev and prod really are different.

**4. EC2 through CI/CD.** This is the one that made me say OH MY GOSH out loud. More on it next.

## The part that almost broke me: SSH keys

Alright, deep breath. In the CI/CD version, a GitHub Actions runner has to log in to my EC2 server on its own. The course never covered this, because Sanjeev used DigitalOcean and just ran a few commands by hand. I wanted to feel how developers push to prod for real.

Here's the catch. A runner is a brand-new throwaway VM every time. EC2 only accepts SSH keys it already trusts, and password login is off. So how does a fresh VM get trusted? You'd think: just generate a keypair on the runner and `ssh-copy-id` it to EC2. But `ssh-copy-id` is itself an SSH login! The runner has no key EC2 trusts, so it can't copy anything. It's a chicken-and-egg problem. Someone has to be trusted first.

So the answer is: you create a keypair yourself, put the public half on EC2, and put the private half in a GitHub secret. And now the scary part: *a private key in the cloud?* Scary right?

Please don't leave me, hear me out!

- It is **not** your personal key. You generate a brand-new keypair used only for this job.
- After you save it in GitHub, you delete it from your laptop. Only GitHub's secret store and the server's public half remain.
- If it ever leaks, the risk is to the EC2 instance (as the `ubuntu` user), not your laptop, because your laptop never trusted that key. And you revoke it by deleting a single line in `authorized_keys`.
- The runner also gets the server's host key fingerprint (`known_hosts`), so it refuses to connect to anything that isn't my server.

Interesting, right? Once this clicked, the rest of the pipeline was just YAML.

## War stories

This is the part I enjoyed writing most, because every one of these cost me an evening.

**The test that never ran.** I broke a test on purpose (changed an assertion from 100 to 101) to prove CI would go red. It stayed green. I had two functions with the same name, `test_deposit`, and Python quietly let the second one replace the first. Linters flag this (`F811`), and I now run one.

**Alembic wiped the wrong database.** My tests use a separate test database, and I told Alembic to use it. But my `env.py` overwrote the URL with the real one on every run. So each test run dropped and rebuilt my real tables, while the test database sat empty. I only noticed when a user I'd inserted by hand vanished. The fix was to let the test pass its URL in and only fall back to the real one when none is given.

**Render's database vanished.** My free Postgres instance on Render expired after about a month, so every new commit redeployed an app with no database to talk to.

**The 409 from Render's deploy hook.** A 409 means "conflict": Render refused the request because a deploy was already running.

**The SSH timeout.** My security group only allowed SSH from my home IP. GitHub's runners come from other addresses, so the deploy job just timed out, with no error that said why. I opened port 22 to the world, with key-only login.

**The empty secret.** My `curl` failed with a malformed URL because the deploy job hadn't declared its environment, so the hook secret arrived empty.

**The Elastic IP bill.** My AWS credits went from $0.20 to $0.90 even though the instance was stopped. An Elastic IP costs money while the instance is off.

**Bugs my tests found.** A `published: false` post came back as `true`, because my create schema didn't have the field. A token for a user who didn't exist still got a 200. A vote removal answered 201 Created. I never would have noticed these by clicking around in Swagger.

## What I'd do next

The pipeline works, but I can already see what I'd improve:

- **Split the jobs** into `test` and `build`, so the Docker job doesn't need the Postgres service or the testing secrets.
- **Back up Postgres** with a daily `pg_dump`. Lab environments can get reset, and a volume isn't a backup.
- **Try a pull-based deploy,** where the server fetches new images itself (a systemd timer or Watchtower), so no private key has to live in GitHub at all.
- **Lock the deploy key down** so it can only run one script.
- **Use short-lived credentials** (AWS SSM or OIDC) instead of a long-lived key, if my account allows it.
- **Handle races properly.** The vote route checks "has this user voted?" and then inserts, so two simultaneous requests could both pass the check. The primary key stops the duplicate, but the user would get a 500 instead of a clean 409, so I'd catch the `IntegrityError`.
- **Roll back easily,** by deploying a commit-SHA tag instead of `latest`.

## Thanks

Huge thanks to freeCodeCamp and Sanjeev Thiyagarajan for publishing a 19-hour course for free. I couldn't have gotten here without it.

If you're thinking about taking the course, do it, but learn some Linux, Docker and database basics first, because it moves fast. And if you want to deploy my project to your own EC2 instance, everything you need is in the README and the deploy guide.

- Course: https://youtu.be/0sOvCWFmrtA
- Live demo: https://my-fast-api-latest.onrender.com/docs
- Deploy guide: Guide: Deploy myFastAPI to your own EC2 with GitHub Actions
- README: README: myFastAPI
