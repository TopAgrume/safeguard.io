# Safeguard.io
<div align="center">
  <img src="assets/safeguard_logo.jpg" alt="Safeguard.io" width="40%" />
</div>

[Safeguard.io](https://t.me/Safeguard_io_bot) is a powerful Telegram bot designed to enhance user safety and well-being through regular check-ins and emergency alerts.
Whether you're traveling alone, working in a high-risk environment, or just want to ensure peace of mind, Safeguard.io is here to help.

Visit our official website [here](https://topagrume.github.io/safeguard.io/).\
Visit the bot on telegram [here](https://t.me/Safeguard_io_bot).

## 📑 Table of Contents
- [Features](#-features)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Optional: Enabling the systemd service](#optional-enabling-the-systemd-service)
- [Usage](#-usage)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

## 🌟 Features

- **Regular Check-ins:** Ensure user well-being with customizable daily verification messages.
- **Emergency Alerts:** Instant notifications to your emergency contacts in case of a problem.
- **Emergency Contact Management:** Easily add, view, and remove emergency contacts.
- **Quick Verification:** Simple verification options for added convenience.
- **Bug Reporting & Feature Suggestions:** Seamlessly report bugs or suggest improvements.

## 🚀 Getting Started

### Prerequisites

Before setting up Safeguard.io, ensure you have the following:

- **Docker and Docker Compose**: For containerized deployment.
- **Python 3.7+**: The bot is built on Python.
- **Telegram Bot Token**: Obtain one from [@BotFather](https://t.me/botfather) on Telegram.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/TopAgrume/safeguard.io
   cd safeguard.io
   ```

2. **Set up environment variables:**

   Create a `.env` file in the root directory with the following content:
   ```bash
   TELEGRAM_API_TOKEN=your_telegram_bot_token
   TELEGRAM_BOT_USERNAME=your_bot_username
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_PORT=5432
   DISCORD_API_TOKEN=your_discord_bot_token (optional)
   DISCORD_CHANNEL_ID=your_discord_channel_id (optional)
   ```

3. **Build and run the Docker containers:**
   ```bash
   docker-compose up -d
   ```

Now, your bot should be up and running!

### [Optional] Enabling the systemd service

1. **Create the systemd service file**:
```sh
sudo cp safeguard_io.service /etc/systemd/system/safeguard_io.service
```

2. **Reload the systemd daemon**:
```sh
sudo systemctl daemon-reload
```

3. **Enable the fan control service to start on boot**:
```sh
sudo systemctl enable safeguard_io.service
```

4. **Start the fan control service**:
```sh
sudo systemctl start safeguard_io.service
```

5. **Check the status of the service**:
```sh
sudo systemctl status safeguard_io.service
```

## 📚 Usage

Once Safeguard.io is running, users can interact with it via Telegram. Below are the essential commands:

### Bot Configuration
- **`/start` or `/subscribe`**: Initiate a conversation with the bot.
- **`/stop` or `/unsubscribe`**: Remove your data and unsubscribe from the service.
- **`/info`**: Get instructions on how to use the bot.

### Emergency Features
- **`/help`**: Send emergency alerts to your contacts.
- **`/undohelp`**: Disable active emergency alerts.

### Managing Emergency Contacts
- **`/addcontact`**: Add an emergency contact.
- **`/showcontacts`**: Display your list of emergency contacts.
- **`/delcontact`**: Delete a specific emergency contact.
- **`/request`**: View received association requests.

### Daily Message Management
- **`/addverif`**: Add a daily verification message.
- **`/showverifs`**: Display your list of daily verifications.
- **`/delverif`**: Delete specific verification messages.
- **`/skip`**: Skip the next verification.
- **`/undoskip`**: Restore the previously skipped verification.
- **`/fastcheck`**: Perform a quick verification.

### Miscellaneous
- **`/bugreport`**: Report bugs or suggest new features.

## 🛠 Tech Stack

- **Python**: Core programming language.
- **Telegram Bot API**: For Telegram bot functionality.
- **PostgreSQL**: Database management.
- **Docker & Docker Compose**: For containerization and orchestration.
- **Discord API**: Used for bug reporting and feedback (optional).

## 🔧 Project Structure

- **`react_chatbot.py`**: Main bot logic and command handlers.
- **`commands.py`**: Command definitions for the bot.
- **`scheduler.py`**: Manages scheduling and sending of daily verification messages.
- **`verif_processing.py`**: Processes verification responses and manages the alert system.
- **`docker-compose.yml`**: Configuration for Docker containers.

## 🤝 Contributing

We welcome contributions! If you have ideas, improvements, or bug fixes, feel free to submit a Pull Request. 

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## 💬 Support

If you encounter issues or have questions, check out the [Issues](https://github.com/TopAgrume/safeguard.io/issues) on our GitHub repository. If your problem isn't listed, feel free to open a new issue.

---

Made with ❤️ by the Safeguard.io team