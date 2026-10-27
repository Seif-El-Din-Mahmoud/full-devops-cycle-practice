# Deployment, rollback and production notes

## How a deploy works
1. A push to `main` runs `CI` (`.github/workflows/ci.yml`): tests, then image build and push to GHCR tagged with the first 7 characters of the commit SHA.
2. The `deploy` job calls `deploy.yml`, which runs `ansible/deploy.yml` against the EC2 host.
3. Ansible logs in to GHCR, writes `/opt/app/.env` with the SHA tag, pulls the image, recreates the service with Docker Compose, and checks `GET /health` on the server.
4. If `/health` does not return 200 after 10 tries, the job prints `docker compose ps` and the container logs, then fails.

## Rollback to the previous known-good SHA
1. Find the last good SHA: open the **Actions** tab, pick the last green `CI` run, and read the 7-character SHA from its commit (or from the repository's **Packages** page, which lists every tag).
2. Open **Actions > Deploy > Run workflow**.
3. Enter that SHA in `image_tag`, leave `break_health` unchecked, and click **Run workflow**.
4. Wait for the run to finish green. Its "Show result" step prints `/health` returning 200 for the rolled-back SHA.

Because every image is tagged with an immutable SHA, a rollback is just a deploy of an older tag. No rebuild is needed.

## Hardening applied
- Container runs as a non-root user (Dockerfile), with a read-only root filesystem, `/tmp` as tmpfs, all Linux capabilities dropped, and `no-new-privileges`.
- The app port is bound to `127.0.0.1` on the server and the security group has no public rule for it. Only SSH is allowed, from specific IPs.
- Port 22 is opened to the GitHub runner's IP only for the duration of the deploy and removed afterwards.

## Production design (not implemented in this lab)
- **Reverse proxy and TLS:** put Nginx, Caddy, or an AWS Application Load Balancer with an ACM certificate in front of the container. The proxy listens on 443, terminates TLS, and forwards to `127.0.0.1:5000`, so the app is never exposed directly.
- **No long-lived credentials:** replace the stored SSH key and AWS access keys with GitHub OIDC (the workflow assumes an IAM role for short-lived credentials) and AWS Systems Manager Session Manager, so no inbound SSH port is needed.