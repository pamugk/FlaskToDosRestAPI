def serialize_single_task(task):
    return '{task}'.format(task=serialize_task(task))

def serialize_task(task):
    return '{{"id": {task.id}, "title":" {task.title}", "description":" {task.description}", "finished": "{task.finished}"}}'.format(task = task)

def serialize_tasks(tasks):
    return '[{0}]'.format(','.join([serialize_task(task) for task in tasks]))

def serialize_task_list(tasks):
    return '{{ {tasks} }}'.format(tasks=serialize_tasks(tasks))