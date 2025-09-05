# gudstatsbot
discord bot for keeping track of Discord notifications for the Gen 3 Pokebot Project.

## Setup
1. Clone the repository
   `cd ~`
   `git clone ...`
3. add your `token`, `guild_id`, `target_user_1 (User ID for Pokebot)`, and `target_channel (Channel ID for the channel Pokebot posts in)` to config.json
   `token` can be found by:
   `guild_id` can be found by:
   `target_user_1` can be found by:
   `target_channel` can be found by:
4. Establish the virtual environment
   `source bot-env/bin/activate`
6. Install the requirements
   `pip install -r requirements.txt`
7. Run the bot
   `python3 main.py`


## Usage Examples
How to enable bot on reboot
`sudo crontab -e` and enter at the bottom of the file: `@reboot cd /home/<user>/gudstatsbot && bot-env/bin/python3 main.py`. Make sure to replace `<user>` with your user

