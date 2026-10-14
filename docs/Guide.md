# Guide: Deploy myFastAPI to your own EC2 with GitHub Actions

Oct 14, 2026 · [@bijesh-09](https://github.com/bijesh-09)

After one-time setup, every push to `main` tests your code, builds and pushes a Docker image, and redeploys it on your own EC2 instance with no manual steps. This guide walks you through that setup from a fresh fork.

## How it works

Each push to `main` runs two jobs in GitHub Actions:

1. **build:** runs pytest against a throwaway Postgres container, then builds the Docker image and pushes it to Docker Hub as `latest` and as the commit SHA.
2. **deploy-ec2** (starts only if `build` passes): the GitHub runner SSHes into your EC2 instance and:
   1. checks that `~/myFastAPI` is a git repo, then runs `git pull --ff-only origin main` (or clones it if it's missing)
   2. stops if `app/.env` is missing
   3. runs `docker compose pull` and `docker compose up -d`, which recreates only the app container and creates postgres container if it doesn't exist
   4. removes unused images to free disk space
   5. checks `http://127.0.0.1:8000/` on the server for up to about 60 seconds and fails the job if the app never responds

**Why deploys queue instead of overlapping.** The job uses a concurrency group (`deploy-ec2`) with `cancel-in-progress: false`. If you push twice quickly, the second run waits for the first to finish. If a third arrives while one is waiting, the waiting one is dropped, so the newest commit always wins. This stops two deploys from running `git pull` and `docker compose up` on the server at the same time.

**Why a private SSH key lives in GitHub.** The runner is a fresh VM every time, and your EC2 instance has password login off by default so it only accepts SSH keys it already trusts. So the runner needs a private key. You'll create a dedicated one just for this job, in [`Step 3`](#step-3-create-a-dedicated-deploy-key).

## Prerequisites

You need an EC2 instance you can SSH into. You can spin it up with any distro you like: Ubuntu, RHEL, Fedora, etc. I have used Ubuntu for this project. Furthermore you need Docker on it, and a Docker Hub account. Check each item before you start.

- **EC2 instance (Ubuntu) with an Elastic IP.** The Elastic IP keeps the address stable across stop and start, so your domain and your `EC2_HOST` variable stay valid.
- **Security group inbound rules.**
  - Port 22 from `0.0.0.0/0`. GitHub-hosted runners use changing IP ranges, so restricting SSH to "my IP" makes the deploy time out. This is only acceptable with key-only login, so confirm it with `sudo sshd -T | grep -E 'passwordauthentication|permitrootlogin'` (you want `no` for password login).
  - Ports 80 and 443 for web traffic.
- **On the server:** `bash`, `git`, `curl`, and Docker with the **Compose v2 plugin** (`docker compose version` must work). Install Docker from the [official Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/).
- **Docker group.** Your SSH user must run Docker without sudo: `sudo usermod -aG docker $USER`, then log out and back in.
- **A Docker Hub account.**
- **A GitHub account,** with Actions enabled on your fork.
- **AWS Access or Academy Learner Lab if you are a student like me.** For the Learner Lab, the instance stops when the lab session ends, so the deploy fails until you start the lab and the instance again. The Elastic IP is billed even while the instance is stopped.

## Step 1: Fork the repo and adjust the names

1. Fork `https://github.com/bijesh-09/myFastAPI` to your account.
2. Open your fork's **Actions** tab and click the button to enable workflows (GitHub disables them on forks by default).
3. **Change the Docker image name in `docker-compose-prod.yml`.** It is hardcoded to `bijesh09/my_fast_api`, so replace `bijesh09` with your Docker Hub username. Without this, your server pulls my image instead of yours. The workflow itself builds `${{ vars.DOCKER_USERNAME }}/my_fast_api`, so you only need to set that variable in Step 4. If you rename the image, change both the `tags:` lines in `.github/workflows/build-deploy.yml` and the `image:` line in the compose file.
4. **Understand the `_test` rule.** The tests connect to a database named `<DATABASE_NAME>_test`, and the workflow creates that database in CI. So set `DATABASE_NAME` to the base name (for example `fastapi`), never to `fastapi_test`, or the tests will look for `fastapi_test_test`.
5. **Create two GitHub environments** under **Settings > Environments**: `testing` and `prod`. The names must match the workflow exactly. If a job names an environment that doesn't exist, GitHub creates an empty one and your secrets will appear blank.

## Step 2: Prepare the server

SSH into your instance with the key you already use, then do the following once.

**1. Clone your fork into exactly `~/myFastAPI`.** The deploy script checks that path and nothing else.

```bash
cd ~
git clone https://github.com/<your-username>/myFastAPI.git
```

**2. Create `app/.env`.** This file is not in git, and the deploy stops if it is missing. Generate a secret key first with `openssl rand -hex 32`, then create the file:

```bash
nano ~/myFastAPI/app/.env
```

```text
# Database (the host name is the Postgres container on Docker's private network)
DATABASE_HOSTNAME=postgres
DATABASE_PORT=5432
DATABASE_PASSWORD=<choose-a-password>
DATABASE_NAME=fastapi
DATABASE_USERNAME=postgres

# Used by the Postgres container itself
POSTGRES_PASSWORD=<same-password-as-above>
POSTGRES_DB=fastapi

# App security
SECRET_KEY=<output of openssl rand -hex 32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

- Never reuse someone else's `SECRET_KEY`. Anyone who knows it can forge login tokens for your server.
- The prod compose file publishes no Postgres port, so only the app container can reach the database.
- `POSTGRES_PASSWORD` only takes effect when the data volume is first created. Changing it later does not change the password inside an existing database.
- Keep comments on their own lines, as above.

**3. Expose the app.** The prod compose file binds the app to `127.0.0.1:8000`, so it is only reachable from the server itself.

- *For a quick test:* change that port line to `"8000:8000"`, open port 8000 in the security group, and visit `http://<elastic-ip>:8000/docs`. Change it back to `127.0.0.1:8000` when you finish, and keep the health check in mind: it works with either binding.
- *For a real setup:* put nginx in front and add HTTPS. Point your domain's A record at the Elastic IP, then:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo nano /etc/nginx/sites-available/myfastapi
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/myfastapi /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.com
```

**4. Optional: start on boot.** The compose file uses `restart: unless-stopped`, so Docker brings the containers back after a reboot by itself. If you also want a systemd unit, save this as `/etc/systemd/system/myfastapi-compose.service` and run `sudo systemctl enable myfastapi-compose`:

```ini
[Unit]
Description=MyFastAPI compose stack
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/myFastAPI
ExecStart=/usr/bin/docker compose -f docker-compose-prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose-prod.yml down

[Install]
WantedBy=multi-user.target
```

## Step 3: Create a dedicated deploy key

The runner needs its own SSH key to log in to your server. Create a brand-new key used for nothing else, run these commands on your own computer, and delete the key files afterwards.

```bash
# 1. Generate the key (no passphrase, because CI can't type one)
ssh-keygen -t ed25519 -f ~/.ssh/ci_deploy_key -N "" -C ci-deploy

# 2. Install the public half on EC2
ssh-copy-id -i ~/.ssh/ci_deploy_key.pub -o IdentityFile=~/.ssh/<your-existing-key> ubuntu@<elastic-ip>

# 3. Test that the new key works on its own
ssh -i ~/.ssh/ci_deploy_key -o IdentitiesOnly=yes ubuntu@<elastic-ip> 'echo ok && whoami'

# 4. Print the private key and copy ALL of it, including the BEGIN and END lines, and save it somewhere else temporarily on your local PC/laptop
cat ~/.ssh/ci_deploy_key

# 5. Get the server's host key line, and save it somewhere else temporarily on your local PC/laptop
ssh-keyscan -t ed25519 <elastic-ip>

# 6. Only after you have saved the secrets in Step 4: delete both key files
shred -u ~/.ssh/ci_deploy_key ~/.ssh/ci_deploy_key.pub
```

**What the flags mean**

- `-t ed25519`: a modern, short key type.
- `-f`: the output file. You get the private key and a `.pub` public key.
- `-N ""`: an empty passphrase.
- `-C ci-deploy`: a label, so you remember what the key is for.

**Why `-o IdentityFile=...` in step 2.** `ssh-copy-id` has to log in to EC2 first, and EC2 has password login disabled, so it needs a key the server already trusts. That is the private key you use to SSH in today. It might be the `.pem` file AWS gave you when you launched the instance, or your own key that you added to the instance. The file extension means nothing to SSH. If you normally connect with a plain `ssh ubuntu@<ip>` and no `-i`, SSH uses a default key, so drop the `-o IdentityFile=...` part.

**Why the runner can't generate its own key.** Adding a key to EC2 needs a login, and the runner has no key EC2 trusts yet. Something has to be trusted first, and that is the key you create here.

**Check the host key.** `ssh-keyscan` asks the network, so confirm its answer against the server itself:

```bash
ssh ubuntu@<elastic-ip> 'cat /etc/ssh/ssh_host_ed25519_key.pub'
```

The key text must match. For the `EC2_KNOWN_HOSTS` secret, use the single line from step 5 that does not start with `#`, for example `<elastic-ip> ssh-ed25519 AAAA...`. This line is public information, but don't paste your whole local `known_hosts` file anywhere.

**Is it safe?** The key was created only for this job. If it ever leaks, someone could log in to your EC2 instance as `ubuntu`, but not to your laptop, which never trusted it. To revoke it, delete its line (the one ending in `ci-deploy`) from `~/.ssh/authorized_keys` on the server. For extra safety, you can restrict the key in `authorized_keys` so it can only run one script, but that requires moving the deploy commands into a script on the server.

## Step 4: Docker Hub token and GitHub secrets

**Docker Hub token.** In Docker Hub, go to **Account settings > Personal access tokens > Generate new token**. Give it a name like `github-actions` and the **Read & Write** permission. Read-only cannot push images, so the build job would fail. Copy the token right away, because it is shown only once. Use a token, never your account password.

**GitHub environments.** In your fork, open **Settings > Secrets and variables > Actions** for repository-level values, and **Settings > Environments** for the two environments. Add the following. Secrets are hidden after saving; variables stay readable.

| Where | Name | Type | Value |
| --- | --- | --- | --- |
| Repository | `DEPLOY_EC2` | Variable | `true` (only needed for the optional guard in [Step 5](#step-5-push-and-watch-the-deploy)) |
| `testing` | `DATABASE_HOSTNAME` | Variable | `localhost` |
| `testing` | `DATABASE_PORT` | Variable | `5432` |
| `testing` | `DATABASE_NAME` | Variable | `fastapi` (not `fastapi_test`) |
| `testing` | `DATABASE_USERNAME` | Variable | `postgres` |
| `testing` | `DATABASE_PASSWORD` | Secret | any throwaway password |
| `testing` | `SECRET_KEY` | Secret | output of `openssl rand -hex 32` |
| `testing` | `ALGORITHM` | Variable | `HS256` |
| `testing` | `ACCESS_TOKEN_EXPIRE_MINUTES` | Variable | `30` |
| `testing` | `DOCKER_USERNAME` | Variable | your Docker Hub username |
| `testing` | `DOCKER_HUB_ACCESS_TOKEN` | Secret | the token you just created |
| `prod` | `EC2_HOST` | Variable | your Elastic IP |
| `prod` | `EC2_USER` | Variable | `ubuntu` |
| `prod` | `EC2_SSH_KEY` | Secret | the full private key from Step 3 |
| `prod` | `EC2_KNOWN_HOSTS` | Secret | the host key line from Step 3 |
| `prod` | `RENDER_DEPLOY_HOOK_URL` | Secret | only if you also deploy to Render |

A job only sees the secrets of the environment it declares, plus repository-level ones. If a secret arrives empty in a log (for example `curl: (3) URL rejected`), the job is almost certainly missing its `environment:` line or the secret is saved in the wrong environment. Variables and secrets are also not passed to workflows triggered by pull requests from forks.

## Step 5: Push and watch the deploy

The workflow already contains the deploy job, so there is nothing to write. Commit your change to `docker-compose-prod.yml` and push to `main`, then open the **Actions** tab. You should see `build` finish first, then `deploy-ec2`. A successful run ends with `App is healthy` in the log, and `http://<elastic-ip>:8000/docs` (or your domain) shows the Swagger UI.

For reference, this is the deploy job. If you want forks that skip EC2 to avoid red runs, add the `if:` line. It uses a repository-level variable on purpose, because environment variables are not available to a job-level `if`.

```yaml
  deploy-ec2:
    needs: [build]
    if: ${{ vars.DEPLOY_EC2 == 'true' }} # You can avoid this line if you want to, and just use environment secrets from github
    runs-on: ubuntu-latest
    environment:
      name: prod
    concurrency:
      group: deploy-ec2
      cancel-in-progress: false
    steps:
      - name: Set up SSH
        env:
          SSH_KEY: ${{ secrets.EC2_SSH_KEY }}
          KNOWN_HOSTS: ${{ secrets.EC2_KNOWN_HOSTS }}
        run: |
          install -m 700 -d ~/.ssh
          echo "$SSH_KEY" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          echo "$KNOWN_HOSTS" > ~/.ssh/known_hosts

      - name: Deploy to EC2
        env:
          HOST: ${{ vars.EC2_HOST }}
          SSH_USER: ${{ vars.EC2_USER }}
          REPO: ${{ github.repository }}
        run: |
          ssh -i ~/.ssh/deploy_key -o ConnectTimeout=15 -o ServerAliveInterval=30 \
            "$SSH_USER@$HOST" "REPO=$REPO bash -s" <<'EOF'
          set -euo pipefail
          APP_DIR="$HOME/myFastAPI"
          COMPOSE="docker compose -f docker-compose-prod.yml"

          if [ -d "$APP_DIR/.git" ]; then
            cd "$APP_DIR"
            git pull --ff-only origin main
          else
            git clone "https://github.com/$REPO.git" "$APP_DIR"
            cd "$APP_DIR"
          fi

          [ -f app/.env ] || { echo "app/.env is missing on the server"; exit 1; }

          $COMPOSE pull
          $COMPOSE up -d --remove-orphans
          docker image prune -af

          for i in $(seq 1 15); do
            if curl -fsS http://127.0.0.1:8000/ >/dev/null; then
              echo "App is healthy"; exit 0
            fi
            sleep 4
          done
          echo "App did not become healthy"
          $COMPOSE logs --tail=50 fastapi
          exit 1
          EOF
```

**Reading the script**

- `ssh -o ConnectTimeout=15` gives up quickly if the server is unreachable. `ServerAliveInterval=30` keeps a long session from being dropped.
- `<<'EOF'` feeds the script to `bash -s` on the server. The quotes stop your local shell from expanding variables, so they expand on the server. `REPO` is passed in explicitly.
- `set -euo pipefail` stops at the first failing command (`-e`), treats unset variables as errors (`-u`), and makes a pipeline fail if any part fails (`pipefail`).
- `[ -d path ]` tests whether a directory exists and `[ -f path ]` whether a file exists.
- `docker image prune -af` deletes images no container uses. Never run `docker volume prune` or `docker compose down -v` here, because that would delete the database volume.
- A failed health check usually means a wrong `.env`, but it can also be a migration or database error. The job prints the last 50 log lines.

**Rolling back.** Every build is also tagged with its commit SHA. To roll back, set the image tag in `docker-compose-prod.yml` on the server to an older SHA and run `docker compose -f docker-compose-prod.yml up -d`.

## Troubleshooting, security and costs

**Troubleshooting**

| What you see | Likely cause | Fix |
| --- | --- | --- |
| `Connection timed out` at the SSH step | Port 22 isn't open to GitHub's runners, the instance is stopped (for example the Learner Lab session ended), or `EC2_HOST` is wrong | Open port 22 (key-only), start the instance, check the Elastic IP |
| `Host key verification failed` | `EC2_KNOWN_HOSTS` is empty or wrong, or the instance was rebuilt and has a new host key | Run `ssh-keyscan -t ed25519 <ip>` again and update the secret |
| `Permission denied (publickey)` | The private key was pasted without its BEGIN and END lines, or the public half isn't in `authorized_keys` | Re-copy the full key, and test it with `-o IdentitiesOnly=yes` |
| `curl: (3) URL rejected`, or a blank value in a log | The job is missing its `environment:` line, or the secret is saved in a different environment | Match the environment name and where the secret lives |
| `app/.env is missing on the server` | Step 2 wasn't finished | Create `~/myFastAPI/app/.env` |
| `App did not become healthy` | Wrong `.env`, or a migration or database error | Read the 50 log lines the job prints, then check `DATABASE_HOSTNAME=postgres` |
| Tests fail with a missing database such as `fastapi_test_test` | `DATABASE_NAME` already ends in `_test` | Set it to `fastapi` |
| `denied: requested access to the resource is denied` when pushing | The Docker Hub token is read-only, or `DOCKER_USERNAME` is wrong | Create a Read & Write token and check the variable |
| The server runs my image, not yours | `docker-compose-prod.yml` still names `bijesh09/my_fast_api` | Change it to your Docker Hub username |
| `git pull` refuses to continue | Someone edited files by hand in `~/myFastAPI` on the server | Run `git status` there and discard or commit the changes |
| Render returns 409 on the hook | A deploy is already running, or auto-deploy is still on | Wait, or turn auto-deploy off for that service |

**Security**

- Port 22 is open to the internet. Keep password login off, and consider `fail2ban`.
- Make sure `.dockerignore` excludes `app/.env`. Your image is public or shared on Docker Hub, and `context: ./` copies everything that isn't ignored. If a secrets file was ever included, rotate those secrets.
- Never run `docker volume prune` or `docker compose down -v` on the server. They delete the database volume.

**Costs and resilience**

- An Elastic IP is billed continuously, including while the instance is stopped. At roughly $0.005 per hour that is about $3.60 a month, but check AWS's current pricing.
- In the Learner Lab the instance stops when the session ends, and your site is down until you restart it.
- Back up the database with a daily `pg_dump`. A Docker volume is not a backup.
- Add log rotation to each service in the compose file so logs don't fill the disk:

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
```
