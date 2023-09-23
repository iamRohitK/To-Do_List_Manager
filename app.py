from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)
tasks = []

class TaskSnapshot:
    def __init__(self, state):
        self.state = state

    def get_state_snapshot(self):
        return self.state

class TaskSnapshotHolder:
    def __init__(self, state):
        self.state = state

    def set_state_snapshot(self, state):
        self.state = state

    def save_to_snapshot(self):
        return TaskSnapshot(self.state)

    def restore_from_snapshot(self, snapshot):
        self.state = snapshot.get_state_snapshot()

class TaskKeeper:
    def __init__(self):
        self.snapshots = []
        self.current_snapshot_index = -1  # Track the current state index

    def get_snapshot(self, index):
        return self.snapshots[index]

    def add_snapshot(self, snapshot):
        # When a new snapshot is added, remove all redo actions
        if self.current_snapshot_index < len(self.snapshots) - 1:
            self.snapshots = self.snapshots[:self.current_snapshot_index + 1]
        self.snapshots.append(snapshot)
        self.current_snapshot_index += 1  # Increment the current state index

    def undo(self):
        if 0 <= self.current_snapshot_index:
            self.current_snapshot_index -= 1  # Move to the previous state
            return self.snapshots[self.current_snapshot_index]

    def redo(self):
        if self.current_snapshot_index < len(self.snapshots) - 1:
            self.current_snapshot_index += 1  # Move to the next state
            return self.snapshots[self.current_snapshot_index]

keeper = TaskKeeper()
class TaskConstructor:
    def __init__(self):
        self.name = None
        self.description = None
        self.due_date = None
        self.tags = []

    def set_name(self, name):
        self.name = name
        return self

    def set_description(self, description):
        self.description = description
        return self

    def set_due_date(self, due_date):
        self.due_date = due_date
        return self

    def add_tag(self, tag):
        self.tags.append(tag)
        return self

    def create_task(self):
        return Task(self.name, self.description, self.due_date, self.tags)

class Task:
    def __init__(self, name, description, due_date=None, tags=None):
        self.id = len(tasks)
        self.name = name
        self.description = description
        self.due_date = due_date
        self.tags = tags or []
        self.completed = False
        self.snapshot_holder = TaskSnapshotHolder(self)

    def mark_as_completed(self):
        self.completed = True

    def mark_as_uncompleted(self):
        self.completed = False

    def save_state_to_snapshot(self):
        return self.snapshot_holder.save_to_snapshot()

    def restore_state_from_snapshot(self, snapshot):
        self.snapshot_holder.restore_from_snapshot(snapshot)

    def __str__(self):
        return f"{self.name} - {self.description} - Due: {self.due_date} - Tags: {', '.join(self.tags)}"


@app.route('/')
def homepage():
    return render_template('index.html')

keeper = TaskKeeper()

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    print(task_id)
    if 0 <= task_id < len(tasks):
        task = tasks[task_id]

        if not task.completed:
            # Task was not completed, complete it
            task.mark_as_completed()

        snapshot = task.save_state_to_snapshot()
        keeper.add_snapshot(snapshot)
        # return redirect(url_for('view_tasks'))
        return redirect(url_for('view_tasks', filter='not_completed' if task.completed else 'completed'))
    else:
        return "Task not found", 404


@app.route('/undo/<int:index>')
def undo_task(index):
    if 0 <= index < len(keeper.snapshots):
        snapshot = keeper.get_snapshot(index)
        task = tasks[index]

        if task.completed:
            # Task was completed, uncomplete it
            task.mark_as_uncompleted()

        task.restore_state_from_snapshot(snapshot)
    return redirect(url_for('view_tasks'))


@app.route('/redo/<int:index>')
def redo_task(index):
    if 0 <= index < len(keeper.snapshots):
        snapshot = keeper.get_snapshot(index)
        task = tasks[index]

        if not task.completed:
            # Task was not completed, complete it
            task.mark_as_completed()

        task.restore_state_from_snapshot(snapshot)
    return redirect(url_for('view_tasks'))


@app.route('/add', methods=['POST'])
def add_task():
    task_name = request.form.get('task')
    task_description = request.form.get('description')
    due_date = request.form.get('due_date')
    tasks.append(TaskConstructor().set_name(task_name).set_description(task_description).set_due_date(due_date).create_task())
    return redirect(url_for('homepage'))


@app.route('/tasks')
def view_tasks():
    filter_param = request.args.get('filter')

    if filter_param == 'completed':
        filtered_tasks = [task for task in tasks if task.completed]
    else:
        filtered_tasks = [task for task in tasks if not task.completed]

    return render_template('tasks.html', tasks=filtered_tasks)


@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    del tasks[task_id]
    return redirect(url_for('view_tasks'))

if __name__ == '__main__':
    app.run(debug=True)
