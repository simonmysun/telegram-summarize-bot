# telegram-summarize-bot

This is a fork of [fernvenue/summarize-telegram-bot](https://github.com/fernvenue/summarize-telegram-bot/tree/ca022f113dd761bb269d63c1559d20cf38d89b69) that summarize link from telegram message using large language models. 

The changes includes:

- Removed some features that I don't need
- Splitted the code into multiple files
- Sending error messages directly to the telegram user
- Added some special handling for URLs, e.g. arxiv to html, I use gpt for the whole text (if it fits), and I use more tokens
- Moved access control to seperated group message controller. 
- Improved throttle handling
- Improved formatting

## Features

- Summarizes first link from any telegram message received
- Simple access control
- Replaces some URLs e.g. X.com, arxiv.org, etc. with better machine-readable URLs
- Deployment with docker or docker compose

## TODO

- [ ] pdf to text
- [ ] image to text
- [ ] summarize long messages
- [ ] YouTube, Bilibili, podcasts to text

## Deployment

- First you need to create a telegram bot and get the token. You can follow the instructions [here](https://core.telegram.org/bots)
- You need access to an openai style API. You will need an API key and an API endpoint.
- Prepare the credentials and the telegram ID you want to allow to use the bot and write them in a `.env` file. You can use the `.env.example` file as a template.
  - `OPENAI_API_URL` and `ADMIN_USER_IDS` is optional
  - `ALLOWED_TELEGRAM_USER_IDS` are comma separated list of telegram user ids that are allowed to use the bot
  - `MAX_INPUT_LENGTH` is the maximum number of characters that will be sent as content to summarize to the LLM API. Note that this does not include the template.
- Modify `prompt_template.txt` to your liking. This is a template to generate the prompt. It should contain the string `{content}` and `{disscussion}` which will be replaced by the content and the discussion of the message respectively.

### With Docker

- With docker-compose:

  Modify the `.env` file and `prompt_template.txt` as described above and specify their paths in the `docker-compose.yml` file.

  ```bash
  docker-compose up -d
  ```

- Without docker-compose:

  Modify the `.env` file and `prompt_template.txt` as described above and specify their paths in the following command.

  ```bash
  docker build -t telegram-summarize-bot https://github.com/simonmysun/telegram-summarize-bot.git
  docker run -d -v /path/to/.env:/app/.env:r -v /path/to/prompt_template.txt:/app/prompt_template.txt:r  --name telegram-summarize-bot --init telegram-summarize-bot
  ```

### Without Docker

#### Clone the Repository

```bash
git clone https://github.com/yourusername/telegram-summarize-bot.git
cd telegram-summarize-bot
```

### Create a Virtual Environment (Optional but recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the root directory of the project and add your credentials. You can use the `.env.example` file as a template.

## Running the Bot

```bash
python bot.py
```

## Usage

- Send a message to the bot with a link in it. The bot will summarize the content of the link and send it back to you.
- Invite the bot to a group chat and it will summarize the first link in any message sent to the group.

## License

This project is licensed under the BSD-3 License. See the [LICENSE](LICENSE) file for details.

