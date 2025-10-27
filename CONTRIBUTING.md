# Contributing to UCS Discord Bot

Thank you for your interest in contributing! We welcome contributions in the form of bug fixes, improvements, documentation, or new features.

---

## How to Contribute

1. **Fork the repository**
   Click the "Fork" button in the top-right corner of this repository.

2. **Clone your fork locally**

```bash
git clone https://github.com/YOUR_USERNAME/ucs-discord-bot.git
cd ucs-discord-bot
````

3. **Create a new branch**

```bash
git checkout -b feature/your-feature-name
```

4. **Make your changes**

   * Python bot code: `bot.py`
   * Documentation updates

5. **Test your changes locally**

   * Make sure the bot runs correctly in Docker:

   ```bash
   docker build -t ucsbot:latest .
   docker run -it --env-file .env -v $(pwd)/data:/app/data ucsbot:latest
   ```

6. **Commit your changes**

```bash
git add .
git commit -m "Add feature: description"
git push origin feature/your-feature-name
```

7. **Open a Pull Request**

   * Go to the main repository and click "New Pull Request".
   * Describe your changes clearly.
   * Submit your PR.

---

## Guidelines

* Follow the existing code style (Python PEP8 for bot, TypeScript/JavaScript style for Astro).
* Keep `.env` and `data/` out of the repository — never commit sensitive tokens or databases.
* Document any new commands or functionality in `README.md`.
* Ensure the bot works with Docker and that the subscription system is unaffected.
