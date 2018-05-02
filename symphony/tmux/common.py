def tmux_name_check(name, resource_type):
    if not name:
        raise ValueError('Empty {} name given.'.format(resource_type))
    elif name.find(':') != -1 or name.find('.') != -1:
        raise ValueError('Tmux {} name cannot contain colon or period.'
                .format(resource_type))

