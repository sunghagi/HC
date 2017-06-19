#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-

def comment_remove(ConfigValueWithComment):
	ConfigValue=ConfigValueWithComment.split('#', 1)[0].strip()
	return ConfigValue
