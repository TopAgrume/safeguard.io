# Safeguard.io

Safeguard.io is a powerful Telegram bot designed to enhance user safety and well-being through regular check-ins and emergency alerts.

## 📑 Table of Contents
- [Features](#-features)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#-usage)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

## 🌟 Features

- Regular check-ins to ensure user well-being
- Emergency alert system
- Customizable daily verification messages
- Emergency contact management
- Quick verification option
- Bug reporting and feature suggestion system

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:
- Docker and Docker Compose
- Python 3.7+
- A Telegram Bot Token (obtain from [@BotFather](https://t.me/botfather) on Telegram)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/TopAgrume/safeguard.io
   cd safeguard.io
   ```

2. Create a `.env` file in the root directory with the following content:
   ```
   TELEGRAM_API_TOKEN=your_telegram_bot_token
   TELEGRAM_BOT_USERNAME=your_bot_username
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_PORT=5432
   DISCORD_API_TOKEN=your_discord_bot_token (optional)
   DISCORD_CHANNEL_ID=your_discord_channel_id (optional)
   ```

3. Build and run the Docker containers:
   ```
   docker-compose up -d
   ```

## 📚 Usage

Once the bot is running, users can interact with it through Telegram. Here are the key commands:

### Bot Configuration
- `/start` or `/subscribe`: Initiate a conversation with the bot
- `/stop` or `/unsubscribe`: Delete personal related data
- `/info`: Receive information on how to use the bot

### Emergency Features
- `/help`: Request emergency assistance from your contacts
- `/undohelp`: Disable emergency alerts

### Managing Emergency Contacts
- `/addcontact`: Add new emergency contacts
- `/showcontacts`: Display your list of emergency contacts
- `/delcontact`: Delete specific emergency contacts
- `/request`: View received association requests

### Daily Message Management
- `/addverif`: Add a daily verification message
- `/showverifs`: Display your list of daily verifications
- `/delverif`: Delete specific daily verifications
- `/skip`: Skip the next verification
- `/undoskip`: Activate the previously skipped verification
- `/fastcheck`: Perform a quick verification

### Miscellaneous
- `/bugreport`: Report bugs or suggest improvements

## 🛠 Tech Stack

- Python
- Telegram Bot API
- PostgreSQL
- Docker & Docker Compose
- Discord API (for bug reports)

## 🔧 Project Structure

The project consists of the following key files:
1. `react_chatbot.py`: Main bot logic and command handlers
2. `commands.py`: Definitions for bot commands
3. `scheduler.py`: Handles scheduling and sending of daily verification messages
4. `verif_processing.py`: Processes verification responses and manages the alert system
5. `docker-compose.yml`: Defines the multi-container Docker application

## Contributing

We welcome contributions to Safeguard.io! If you have suggestions for improvements or bug fixes, please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please:
1. Check the existing [Issues](https://github.com/TopAgrume/safeguard.io/issues) on our GitHub repository
2. If your issue isn't already listed, feel free to open a new issue
3. For urgent matters, contact us at support@safeguard.io

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Made with ❤️ by the Safeguard.io team