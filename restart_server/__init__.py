import time
from threading import Event

from mcdreforged.api.all import *


class Config(Serializable):
	restart_delay: int = 10
	permission: int = 3


PLUGIN_METADATA = ServerInterface.get_instance().as_plugin_server_interface().get_self_metadata()
restart_event = Event()
unrestart_event = Event()
config = Config.get_default()


def tr(translation_key: str, *args, **kwargs) -> RTextMCDRTranslation:
	return ServerInterface.get_instance().rtr('{}.{}'.format(PLUGIN_METADATA.id, translation_key), *args, **kwargs)

@new_thread(PLUGIN_METADATA.name + ' - unrestart')
def unrestart(source: CommandSource):
	if not source.has_permission(config.permission):
		source.reply(RText(tr('permission.need_permission'), color=RColor.red))
		return

	if not restart_event.isSet():
		source.reply(tr('restart.no'))
		return

	if unrestart_event.isSet():
		return
	
	unrestart_event.set()
	


@new_thread(PLUGIN_METADATA.name + ' - restart')
def restart(source: CommandSource):
	if not source.has_permission(config.permission):
		source.reply(RText(tr('permission.need_permission'), color=RColor.red))
		return

	eve = restart_event.isSet();
	restart_event.set()
	if eve:
		source.reply(tr('restart.spam'))
		return

	try:
		for i in range(config.restart_delay):
			source.get_server().broadcast(RText(tr('restart.countdown', config.restart_delay - i), color=RColor.red))
			time.sleep(1)

			if unrestart_event.isSet():
				source.get_server().broadcast(RText(tr('restart.cancel'), color=RColor.red))
				return

		source.get_server().restart()
	finally:
		unrestart_event.clear()
		restart_event.clear()

@new_thread(PLUGIN_METADATA.name + ' - reload')
def reload(source: CommandSource):
	if not source.has_permission(config.permission):
		source.reply(RText(tr('permission.need_permission'), color=RColor.red))
		return

	source.get_server().execute('reload')
	source.reply(RText(tr('reload.info'), color=RColor.green))


def on_load(server: PluginServerInterface, prev):
	try:
		global restart_event
		global unrestart_event

		assert type(prev.restart_event) is type(restart_event)
		assert type(prev.unrestart_event) is type(unrestart_event)

		restart_event = prev.restart_event
		unrestart_event = prev.unrestart_event

	except (AttributeError, AssertionError):
		pass

	global config
	config = server.load_config_simple(target_class=Config)

	server.register_help_message('!!restart', tr('help.restart', config.restart_delay))
	server.register_help_message('!!unrestart', tr('help.unrestart'))
	server.register_help_message('!!reload', tr('help.reload'))

	server.register_command(Literal('!!restart').runs(restart))
	server.register_command(Literal('!!unrestart').runs(unrestart))
	server.register_command(Literal('!!reload').runs(reload))
