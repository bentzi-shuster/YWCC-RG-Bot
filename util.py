import discord
import re


class Util():
    """Utility class for processing messages and sending replies in Discord."""

    def __init__(self, client, guild):
        """Initialize the Util class with a Discord client and guild."""
        self.user_dict = {}
        self.client = client
        self.idxs = {}
        self.idx = 1
        self.last_ts = None
        self.guild = guild

    def get_name(self, id: int):
        """Get the name of a user by their ID. If the name is not cached, fetch it from the guild."""
        if id in self.user_dict:
            return self.user_dict[id]
        name = self.guild.get_member(id).nick
        name = name if name != None else self.client.get_user(
            id).display_name + "*"
        self.user_dict[id] = name
        return name

    def format_time_difference(self, start, end):
        """ Calculate the difference between two datetime objects"""
        delta = end - start
        total_seconds = int(delta.total_seconds())
        # Determine the time units to use for the difference
        if abs(total_seconds) < 60:
            return f"{total_seconds:+d} sec"
        elif abs(total_seconds) < 3600:
            minutes = total_seconds // 60
            return f"{minutes:+d} min"
        elif abs(total_seconds) < 86400:
            hours = total_seconds // 3600
            return f"{hours:+d} h"
        else:
            days = total_seconds // 86400
        return f"{days:+d} d"

    def process_text(self, str):
        """Process a message text, replacing user pings with their names."""
        def replace_ping(match):
            """Replace a user ping with their name."""
            indices = match.regs[1]
            return '@' + self.get_name(int(match.string[indices[0]:indices[1]]))
        return re.sub(r'<@(\d+)>', replace_ping, str)

    def process(self, message: discord.Message):
        """Process a message, returning a formatted string representation of it."""
        self.idxs[message.id] = self.idx
        line = f"{self.idx}: "
        if self.last_ts != None:
            line += self.format_time_difference(self.last_ts,
                                                message.created_at)

        name = self.get_name(message.author.id)
        line += f" [{name}]: "

        if message.reference != None:
            line += f"(replyto: Msg {self.idxs.get(message.reference.message_id, '?')}) "

        line += self.process_text(message.content) + "\n"

        self.last_ts = message.created_at
        self.idx += 1
        return line

    def get_idx(self):
        """Getter for the idx variable"""
        return self.idx

    async def batch_reply(self, interaction: discord.Interaction, report: str):
        """Send a message in multiple parts if it exceeds the character limit."""
        if len(report) <= 2000:
            await interaction.followup.send(report)
        else:
            interacted = False
            # Split the string into lines, preserving line breaks
            lines = report.splitlines(keepends=True)
            current_chunk = ""

            async def send(text):
                nonlocal interacted, interaction
                if not interacted:
                    await interaction.followup.send(text)
                    interacted = True
                else:
                    await interaction.channel.send(text)

            for line in lines:
                if len(current_chunk) + len(line) > 2000:
                    await send(current_chunk)
                    current_chunk = line
                else:
                    current_chunk += line
            await send(current_chunk)

    async def get_annon_id(self, user_hash, user_id):
        """add a users hash to the file"""
        # if the file does not exist, create it
        try:
            with open("db.txt", "r") as file:
                pass
        except FileNotFoundError:
            with open("db.txt", "w") as file:
                pass

        with open("db.txt", "r") as file:
            lines = file.readlines()
            # check if the user is already in the file
            for line in lines:
                if user_hash in line:
                    # return the line number
                    return lines.index(line)
            # add the user to the file
            lines.append(user_hash + " " + user_id + "\n")
        with open("db.txt", "w") as file:
            file.writelines(lines)
        return len(lines) - 1

    async def get_user(self, row):
        """get a users id from the hash"""
        try:
            with open("db.txt", "r") as file:
                pass
        except FileNotFoundError:
            with open("db.txt", "w") as file:
                pass
        with open("db.txt", "r") as file:
            lines = file.readlines()
            return lines[row].split(" ")[1] or None

    def convert_mentions_to_string(self, message: discord.Message):
        """Convert mentions in a message to string representations."""
        user_mentions = message.mentions
        role_mentions = message.role_mentions
        ping_regex = re.compile(r"<@!?(\d+)>")
        for user in user_mentions:
            message.content = message.content.replace(
                f"<@{user.id}>", user.name)
        for role in role_mentions:
            message.content = message.content.replace(
                f"<@&{role.id}>", role.name)
        message.content = message.content.replace("@everyone", "everyone")
        message.content = message.content.replace("@here", "here")
        # this will replace any other mentions with someone
        message.content = re.sub(ping_regex, "unknown user", message.content)
        return message
