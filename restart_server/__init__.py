import time
from threading import Event, Lock

from mcdreforged.api.all import *


class Config(Serializable):
	restart_delay: int = 10
	permission: int = 4


PLUGIN_METADATA = ServerInterface.get_instance().as_plugin_server_interface().get_self_metadata()
restart_event = Event()
unrestart_event = Event()
killrst_event = Event()
event_lock = Lock()
config = Config.get_default()


def tr(translation_key: str, *args, **kwargs) -> RTextMCDRTranslation:
	return ServerInterface.get_instance().rtr('{}.{}'.format(PLUGIN_METADATA.id, translation_key), *args, **kwargs)

def chk_permissions(source: CommandSource):
	if not source.has_permission(config.permission):
		source.reply(RText(tr('permission.need_permission'), color=RColor.red))
		return False
	return True

def set_event():
	with event_lock:
		if restart_event.is_set():
			return False
		restart_event.set()
		return True

def unset_event():
	with event_lock:
		unrestart_event.clear()
		restart_event.clear()

@new_thread(PLUGIN_METADATA.name + ' - unrestart')
def unrestart(source: CommandSource):
	if not chk_permissions(source):
		return
	
	with event_lock:
		if not restart_event.is_set():
			source.reply(tr('restart.no'))
			unrestart_event.clear()
			return
		unrestart_event.set()

@new_thread(PLUGIN_METADATA.name + ' - restart')
def restart(source: CommandSource):
	if not chk_permissions(source):
		return

	if not set_event():
		source.reply(tr('restart.spam'))
		return

	try:
		for i in range(config.restart_delay):
			source.get_server().broadcast(RText(tr('restart.countdown', config.restart_delay - i), color=RColor.red))
			time.sleep(1)

			if unrestart_event.is_set():
				source.get_server().broadcast(RText(tr('restart.cancel'), color=RColor.red))
				return

		is_restart = source.get_server().restart()
		if not is_restart:
			source.get_server().logger.error(tr('restart.fail'))
			source.reply(RText(tr('restart.fail')))
	finally:
		unset_event()
		
@new_thread(PLUGIN_METADATA.name + ' - killrst')
def killrst(source: CommandSource):
	if not chk_permissions(source):
		return
	
	if not set_event():
		source.reply(tr('restart.spam'))
		return
	
	try:
		is_kill = source.get_server().kill()
		if is_kill:
			killrst_event.set()#设置事件，等待服务端停止
		else:
			source.get_server().logger.error(tr('killrst.fail'))
			source.reply(RText(tr('killrst.fail')))
	finally:
		unset_event()


@new_thread(PLUGIN_METADATA.name + ' - fastrst')
def fastrst(source: CommandSource):
	if not chk_permissions(source):
		return
	
	if not set_event():
		source.reply(tr('restart.spam'))
		return
	
	try:
		is_restart = source.get_server().restart()
		if not is_restart:
			source.get_server().logger.error(tr('restart.fail'))
			source.reply(RText(tr('restart.fail')))
	finally:
		unset_event()
	

def on_server_stop(server: PluginServerInterface, server_return_code: int):
	if killrst_event.is_set():  # 如果设置了事件，则重启，然后清除
		is_start = server.start()
		if not is_start:
			server.logger.error(tr('restart.fail'))
		killrst_event.clear()
	

@new_thread(PLUGIN_METADATA.name + ' - reload')
def reload(source: CommandSource):
	if not chk_permissions(source):
		return

	source.get_server().execute('reload')
	source.reply(RText(tr('reload.info'), color=RColor.green))


def on_load(server: PluginServerInterface, prev):
	try:
		global restart_event
		global killrst_event
		global unrestart_event
		global event_lock

		assert type(prev.restart_event) is type(restart_event)
		assert type(prev.killrst_event) is type(killrst_event)
		assert type(prev.unrestart_event) is type(unrestart_event)
		assert type(prev.event_lock) is type(event_lock)

		restart_event = prev.restart_event
		killrst_event = prev.killrst_event
		unrestart_event = prev.unrestart_event
		event_lock = prev.event_lock

	except (AttributeError, AssertionError):
		pass

	global config
	config = server.load_config_simple(target_class=Config)

	server.register_help_message('!!restart', tr('help.restart', config.restart_delay))
	server.register_help_message('!!fastrst', tr('help.fastrst'))
	server.register_help_message('!!killrst', tr('help.killrst'))
	server.register_help_message('!!unrestart', tr('help.unrestart'))
	server.register_help_message('!!reload', tr('help.reload'))

	server.register_command(Literal('!!restart').runs(restart))
	server.register_command(Literal('!!fastrst').runs(fastrst))
	server.register_command(Literal('!!killrst').runs(killrst))
	server.register_command(Literal('!!unrestart').runs(unrestart))
	server.register_command(Literal('!!reload').runs(reload))
	
def on_unload(server: PluginServerInterface):
	unset_event()