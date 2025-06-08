# MCDR_Restart-Server
MCDR插件，用于快速重启服务器

使用命令!!restart以重启服务器

重启倒计时过程使用!!unrestart取消重启

使用指令!!reload重新加载

使用指令!!fastrst立刻重启

使用指令!!killrst杀掉服务端后重启（用于特殊情况）

在!!restart倒计时过程中不允许其它重启指令重入，除非取消（确保安全）

由Fallen_Breath的[SimpleOP](https://github.com/MCDReforged/SimpleOP)插件修改而来

去掉了!!op指令，并新增了对所有指令的权限等级检查

指令默认权限等级为4，可以在配置文件中修改权限等级

重启倒计时默认为10s，可以在配置文件中修改重启倒计时

