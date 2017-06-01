# Exam reminder bot based on the example bot of Joel Rosdahl.

import ssl
import sys
import irc.connection
import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr

import handler
import utils

class ExamBot(irc.bot.SingleServerIRCBot):

    def __init__(self, channels, nickname, server, port, password,
     command_prefix, bridge_nick, help_text, **args):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname,
         nickname, **args)
        self._command_prefix = command_prefix
        self._channels = channels
        self.__nickname = nickname
        self.__password = password
        self.__bridge_nick = bridge_nick
        self.__handler = handler.ExamBotCommandHandler(help_text, self.__nickname)

    def on_nicknameinuse(self, c, e):
        """ If nick in use, add underscore.
        """
        c.nick(c.get_nickname() + "_")


    def on_welcome(self, c, e):
        """ Identify with NickServ and join the channels.
        """
        c.privmsg("NickServ", "IDENTIFY " + self.__password)
        for channel in self._channels:
            c.join(channel)


    def on_privmsg(self, c, e):
        """ dogexam does not respond to private messages, as private exam
            reminders are less compelling.
        """
        pass


    def on_pubmsg(self, c, e):
        """ Channel message handler, with support for a fixed bridging nick
            connecting IRC with other chat platforms. This requires the bridge
            bot to emit message on IRC in the form of '<sender> PREFIX COMMAND'.
            If no command is supplied with the command prefix, the default
            action is to display the time until the next exam.
        """

        channel = e.target
        return_message = ""

        # Bridged messages.
        if e.source.nick.startswith(self.__bridge_nick):
            bridge_split = e.arguments[0].split(" ", 2)
            bridge_split[0] = bridge_split[0].strip()
            if bridge_split[1] == self._command_prefix and
             bridge_split[0].startswith('<') and bridge_split[0].endswith('>'):
                source_nick = bridge_split[0][1:-1] # The actual sender.
                if len(a) > 2:
                    return_message = self.__handler.do_command(
                     bridge_split[2].strip(), source_nick)
                else:
                    return_message = self.__handler.do_command("next",
                     source_nick)

        # Regular IRC messages.
        else:
            regular_split = e.arguments[0].split(" ", 1)
            if irc.strings.lower(regular_split[0]) == self._command_prefix:
                if len(regular_split) > 1:
                    return_message = self.__handler.do_command(
                     regular_split[1].strip(), e.source.nick)
                else:
                    return_message = self.__handler.do_command(
                     "next", e.source.nick)

        # If there's any response, send response with notice.
        if return_message != "":
            self.connection.notice(channel, return_message)

        return True


    def on_dccmsg(self, c, e):
        """ Decode DCC message if received. """

        text = e.arguments[0].decode('utf-8')


    def on_dccchat(self, c, e):
        """ Acknowledge DCC sessions. """

        if len(e.arguments) != 2:
            return
        args = e.arguments[1].split()
        if len(args) == 4:
            try:
                address = ip_numstr_to_quad(args[2])
                port = int(args[3])
            except ValueError:
                return
            self.dcc_connect(address, port)


# Run a bot instance.
def make_bot(config_file):
    """ Main entry point to start a bot instance. """

    config = utils.read_config(config_file)

    if config['irc_use_tls']:
        ssl_factory = {'connect_factory': irc.connection.Factory(wrapper=ssl.wrap_socket)}
    else:
        ssl_factory = {}

    dog = ExamBot(config['irc_channels'], config['irc_nickname'],
     config['irc_server'], config['irc_port'], config['irc_password'],
     config['command_prefix'], config['slack_bridge_nick_prefix'],
     config['help_text'], **ssl_factory)

    bot.start()

if __name__ == "__main__":
    make_bot('config/config.json')
