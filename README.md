# Lights Out Bot

## Description

A plain and simple Telegram bot which notifies the authorized users when the lights are turned off.

## Installation

Install the dependencies:

```bash
pip3 install -r requirements.txt
```

Run the bot:

```bash
python3 main.py
```

## Configuration
Create an '.env' file in the same directory as the 'main.py' file and add the following variables:

- TELEGRAM_TOKEN
- BOT_MYSQL_HOST
- BOT_MYSQL_PORT
- BOT_MYSQL_USER
- BOT_MYSQL_PASS

## Database
The bot uses a MySQL database to store the user info as well as power outage data. The database can be created using the following SQL query:

```sql
CREATE DATABASE lightsout DEFAULT CHARACTER SET utf8mb4;
CREATE TABLE power_outages (
  id int NOT NULL AUTO_INCREMENT,
  time_started datetime DEFAULT NULL,
  time_ended datetime DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY id_UNIQUE (id)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE telegram_authorized_users (
  user_id int unsigned NOT NULL,
  user_name varchar(100) DEFAULT NULL,
  PRIMARY KEY (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE telegram_subscribers (
  user_id int unsigned NOT NULL,
  PRIMARY KEY (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```