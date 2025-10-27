# Infoloom Discord Bot

A Discord bot that notifies channels about upcoming evaluations for university courses (UCs) based on a JSON dataset from the Infoloom App. Built with Python (`discord.py`).

---

## Features

- Responds to commands using the prefix `+`.
- Show upcoming evaluations (`+proximas [days]`).
- Display detailed UC information (`+uc <slug|sigla>`).
- Subscribe channels to notifications for specific UCs (`+subscrever <slug> [days-before]`).
- Cancel subscriptions (`+cancelar <slug>`).
- List all subscriptions for the channel (`+listar`).
- Automatic notifications based on the configured days-before interval.

---

## Requirements

- Docker (for containerized bot deployment)
- Discord account and server with permissions to add a bot
- Node.js (for Astro API)
- Python 3.11+

---

## Setup

### 1. Astro API

Make sure your UCS JSON file is available via the Astro API:

```ts
// Example endpoint: src/pages/api/ucs.ts
import fs from "fs";
import type { APIRoute } from "astro";

export const GET: APIRoute = async () => {
  const data = fs.readFileSync(new URL("../../public/data/ucs.json", import.meta.url), "utf-8");
  return new Response(data, {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
};
````

Deploy your Astro project to Vercel or another hosting service.

---

### 2. Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications) and create a new application.
2. Add a Bot and copy the **TOKEN**.
3. Enable **Message Content Intent** under "Privileged Gateway Intents".
4. Generate an invite URL with the `bot` scope and permissions:

   * `Send Messages`
   * `Read Messages/View Channels`
   * `Embed Links`
   * `Read Message History`

---

### 3. Bot Setup

1. Clone this repository.
2. Create a `.env` file in the project root:

```
DISCORD_TOKEN=YOUR_NEW_TOKEN
UCS_API_URL=https://yourdomain.com/api/ucs
CHECK_INTERVAL_MINUTES=60
DB_PATH=/app/data/subscriptions.db
```

3. Build and run the Docker container:

```bash
docker build -t ucsbot:latest .
docker run -d --name ucsbot --env-file .env -v $(pwd)/data:/app/data ucsbot:latest
```

---

### 4. Commands

| Command                            | Description                                               |
| ---------------------------------- | --------------------------------------------------------- |
| `+ajuda`                           | Shows a list of all available commands                    |
| `+proximas [days]`                 | Lists upcoming evaluations in the next `days` (default 7) |
| `+uc <slug \| sigla>`              | Shows detailed information about a specific UC            |
| `+subscrever <slug> [days-before]` | Subscribes the channel for notifications for a UC         |
| `+cancelar <slug>`                 | Cancels a subscription for a UC                           |
| `+listar`                          | Lists all subscriptions for the channel                   |

---

### 5. Notes

* Subscriptions are **per channel**, not per user.
* Notifications are sent automatically according to `CHECK_INTERVAL_MINUTES`.
* The bot stores subscriptions in SQLite (`subscriptions.db`) for persistence.
* Make sure your bot has access to the channels you want to notify.
