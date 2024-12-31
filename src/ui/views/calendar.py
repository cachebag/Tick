from textual.containers import Container, Grid, Horizontal, Vertical
from textual.widgets import Button, Input, Label, Static, TextArea
from textual.screen import ModalScreen
from textual import on
from textual.app import ComposeResult
from datetime import datetime
import calendar
from ...widgets.task_widget import Task
from textual.binding import Binding
from src.ui.mixins.focus_mixin import InitialFocusMixin
from typing import Optional
from textual.widget import Widget

class NavBar(Horizontal):
    def __init__(self, current_date: datetime):
        super().__init__()
        self.current_date = current_date
        self.styles.width = "100%"
        self.styles.height = "5"
        self.styles.align = ("center", "middle")

    def compose(self) -> ComposeResult:
        prev_btn = Button("\u25C4 \n \n", id="prev_month", classes="calendar-nav-left")
        next_btn = Button("\u25BA", id="next_month", classes="calendar-nav-right")
        header = CalendarHeader(self.current_date)
        header.styles.width = "100%"
        header.styles.margin = (0, 5)

        yield prev_btn
        yield header
        yield next_btn

class CalendarDayButton(Button):
    def __init__(self, day: int, is_current: bool = False) -> None:
        super().__init__(str(day))
        self.day = day
        self.is_current = is_current
        self.styles.content_align = ("center", "middle")
        self.styles.width = "100%"
        self.styles.height = "100%"
        if is_current:
            self.add_class("current-day")

class CalendarHeader(Static):
    def __init__(self, current_date: datetime):
        month_year = current_date.strftime('%B %Y')
        super().__init__(month_year)
        self.styles.text_align = "center"
        self.styles.width = "100%"
        self.styles.text_style = "bold"

class CalendarGrid(Grid):
    def __init__(self, current_date: datetime | None = None):
        super().__init__()
        self.current_date = current_date or datetime.now()
        self.styles.height = "85%"
        self.styles.width = "100%"
        self.styles.grid_size_rows = 7
        self.styles.grid_size_columns = 7
        self.styles.padding = 1

    def compose(self) -> ComposeResult:
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for day in weekdays:
            header = Static(day, classes="calendar-weekday")
            header.styles.width = "100%"
            header.styles.height = "100%"
            header.styles.content_align = ("center", "middle")
            yield header

        month_calendar = calendar.monthcalendar(
            self.current_date.year,
            self.current_date.month
        )

        today = datetime.now()

        for week in month_calendar:
            for day in week:
                if day == 0:
                    empty_day = Static("", classes="calendar-empty-day")
                    empty_day.styles.width = "100%"
                    empty_day.styles.height = "100%"
                    yield empty_day
                else:
                    is_current = (day == today.day and
                                self.current_date.month == today.month and
                                self.current_date.year == today.year)
                    day_btn = CalendarDayButton(day, is_current)
                    if is_current:
                        day_btn.focus()
                    yield day_btn

class CalendarView(Container):

    BINDINGS = [
        Binding("up", "move_up", "Up", show=True),
        Binding("down", "move_down", "Down", show=True),
        Binding("left", "move_left", "Left", show=True),
        Binding("right", "move_right", "Right", show=True),
    ]

    def compose(self) -> ComposeResult:
        self.current_date = datetime.now()
        yield NavBar(self.current_date)
        yield CalendarGrid(self.current_date)
        yield DayView(self.current_date)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "prev_month":
            year = self.current_date.year
            month = self.current_date.month - 1
            if month < 1:
                year -= 1
                month = 12
            self.current_date = self.current_date.replace(year=year, month=month, day=1)
            self._refresh_calendar()
            event.stop()

        elif button_id == "next_month":
            year = self.current_date.year
            month = self.current_date.month + 1
            if month > 12:
                year += 1
                month = 1
            self.current_date = self.current_date.replace(year=year, month=month, day=1)
            self._refresh_calendar()
            event.stop()

        elif isinstance(event.button, CalendarDayButton):
            selected_date = self.current_date.replace(day=event.button.day)
            day_view = self.query_one(DayView)
            day_view.set_date(selected_date)

            self.query_one(CalendarGrid).styles.display = "none"
            self.query_one(NavBar).styles.display = "none"
            day_view.styles.display = "block"
            event.stop()

        elif button_id == "save_notes":
            day_view = self.query_one(DayView)
            event.stop()
            day_view.refresh_tasks()

        elif button_id == "add-task":
            event.stop()

        else:
            self.query_one(CalendarGrid).styles.display = "block"
            self.query_one(NavBar).styles.display = "block"
            self.query_one(DayView).styles.display = "none"
            self._refresh_calendar()
            event.stop()

    def action_back_to_calendar(self) -> None:
        day_view = self.query_one(DayView)
        day_view.styles.display = "none"
        self.query_one(CalendarGrid).styles.display = "block"
        self.query_one(NavBar).styles.display = "block"
        self._refresh_calendar()

    def _refresh_calendar(self) -> None:
        self.query("NavBar").first().remove()
        self.query("CalendarGrid").first().remove()
        self.mount(NavBar(self.current_date))
        self.mount(CalendarGrid(self.current_date))


    async def action_move_up(self) -> None:
        current = self.app.focused
        if isinstance(current, CalendarDayButton):
            all_buttons = list(self.query(CalendarDayButton))
            current_idx = all_buttons.index(current)
            if current_idx >= 7:  
                all_buttons[current_idx - 7].focus()

    async def action_move_down(self) -> None:
        current = self.app.focused
        if isinstance(current, CalendarDayButton):
            all_buttons = list(self.query(CalendarDayButton))
            current_idx = all_buttons.index(current)
            if current_idx + 7 < len(all_buttons):  
                all_buttons[current_idx + 7].focus()

    async def action_cycle_focus(self) -> None:
        current = self.app.focused
        focusable = list(self.query("Button"))
        if focusable and current in focusable:
            idx = focusable.index(current)
            next_idx = (idx + 1) % len(focusable)
            focusable[next_idx].focus()
        elif focusable:
            focusable[0].focus()

    async def action_back(self) -> None:
        day_view = self.query_one(DayView)
        if day_view and day_view.styles.display == "block":
            self.action_back_to_calendar()

    def action_focus_previous(self) -> None:
        """Only allow menu navigation when menu is visible"""
        try:
            menu = self.app.screen.query_one("MainMenu")
            if "hidden" in menu.classes:
                return
        except Exception:
            pass

    def action_focus_next(self) -> None:
        """Only allow menu navigation when menu is visible"""
        try:
            menu = self.app.screen.query_one("MainMenu")
            if "hidden" in menu.classes:
                return
        except Exception:
            pass

    def get_initial_focus(self) -> Optional[Widget]:
        """Return the calendar grid as the default focus target"""
        calendar_grid = self.query_one(CalendarGrid)
        # Find first day button in grid
        day_button = calendar_grid.query_one(CalendarDayButton)
        return day_button if day_button else calendar_grid

class TaskForm(ModalScreen):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("f1", "submit", "Submit"),
        Binding("tab", "next_field", "Next Field")
    ]

    def __init__(self, date: datetime) -> None:
        super().__init__()
        self.date = date

    def compose(self) -> ComposeResult:
        with Container(classes="task-form-container"):
            with Vertical(classes="task-form"):
                yield Static("Add New Task", classes="form-header")
                
                yield Static(f"Date: {self.date.strftime('%B %d, %Y')}", classes="selected-date")

                with Vertical():
                    yield Label("Title")
                    yield Input(placeholder="Enter task title", id="task-title")

                with Vertical():
                    yield Label("Due Time")
                    yield Input(placeholder="HH:MM", id="task-time")

                with Vertical():
                    yield Label("Description (optional)")
                    yield TextArea(id="task-description")

                with Horizontal(classes="form-buttons"):
                    yield Button("Cancel", variant="error", id="cancel")
                    yield Button("Add Task", variant="success", id="submit")

    async def action_cancel(self) -> None:
        self.app.pop_screen()
        
    async def action_submit(self) -> None:
        self._submit_form()
        
    async def action_next_field(self) -> None:
        current = self.app.focused
        fields = list(self.query("Input, TextArea, Button"))
        if fields and current in fields:
            idx = fields.index(current)
            next_idx = (idx + 1) % len(fields)
            fields[next_idx].focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
        elif event.button.id == "submit":
            self._submit_form()

    def _submit_form(self) -> None:
        title = self.query_one("#task-title", Input).value
        time = self.query_one("#task-time", Input).value
        description = self.query_one("#task-description", TextArea).text

        if not title or not time:
            self.notify("Title and Time are required", severity="error")
            return

        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            self.notify("Invalid time format", severity="error")
            return

        date = self.date.strftime('%Y-%m-%d')

        task_id = self.app.db.add_task(
            title=title,
            due_date=date,
            due_time=time,
            description=description
        )

        task = {
            "id": task_id,
            "title": title,
            "due_date": date,
            "due_time": time,
            "description": description
        }

        self.dismiss(task)

        try:
            day_view = self.app.screen.query_one(DayView)
            if day_view:
                day_view.refresh_tasks()
                self.notify("Task added successfully!")
        except Exception:
            pass
            
        try:
            from .welcome import TodayContent
            today_content = self.app.screen.query_one(TodayContent)
            if today_content:
                today_content.refresh_tasks()
        except Exception:
            pass 

class TaskEditForm(TaskForm):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("f1", "submit", "Submit"),
        Binding("tab", "next_field", "Next Field"),
        Binding("delete", "delete_task", "Delete Task")
    ]

    def __init__(self, task_data: dict):
        super().__init__(date=datetime.strptime(task_data['due_date'], '%Y-%m-%d'))
        self.task_data = task_data

    def compose(self) -> ComposeResult:
        with Container(classes="task-form-container"):
            with Vertical(classes="task-form"):
                yield Static("Edit Task", classes="form-header")

                with Vertical():
                    yield Label("Title")
                    yield Input(value=self.task_data['title'], id="task-title")

                with Vertical():
                    yield Label("Due Time")
                    yield Input(value=self.task_data['due_time'], id="task-time")

                with Vertical():
                    yield Label("Description (optional)")
                    yield TextArea(self.task_data['description'], id="task-description")

                with Horizontal(classes="form-buttons"):
                    yield Button("Delete", variant="error", id="delete")
                    yield Button("Cancel", variant="primary", id="cancel")
                    yield Button("Save", variant="success", id="submit")


    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            event.stop()
            # self.app.pop_screen() I'm not sure why but adding this breaks the screen
        elif event.button.id == "delete":
            self.app.db.delete_task(self.task_data['id'])
            self.dismiss(None)
            
            try:
                day_view = self.app.screen.query_one(DayView)
                if day_view:
                    day_view.refresh_tasks()
            except Exception:
                pass
                
            try:
                from .welcome import TodayContent
                today_content = self.app.screen.query_one(TodayContent)
                if today_content:
                    today_content.refresh_tasks()
            except Exception:
                pass
                
            self.notify("Task deleted successfully!")
            event.stop()
        elif event.button.id == "submit":
            self._submit_form()
            event.stop()

    def _submit_form(self) -> None:
        title = self.query_one("#task-title", Input).value
        time = self.query_one("#task-time", Input).value
        description = self.query_one("#task-description", TextArea).text

        if not title or not time:
            self.notify("Title and Time are required", severity="error")
            return

        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            self.notify("Invalid time format", severity="error")
            return

        task_id = self.app.db.update_task(
            self.task_data['id'],
            title=title,
            due_date=self.date.strftime('%Y-%m-%d'),
            due_time=time,
            description=description
        )

        task = {
            "id": task_id,
            "title": title,
            "due_date": self.date.strftime('%Y-%m-%d'),
            "due_time": time,
            "description": description
        }

        self.dismiss(task)
        
        try:
            day_view = self.app.screen.query_one(DayView)
            if day_view:
                day_view.refresh_tasks()
                self.notify("Task updated successfully!")
        except Exception:
            pass
            
        try:
            from .welcome import TodayContent
            today_content = self.app.screen.query_one(TodayContent)
            if today_content:
                today_content.refresh_tasks()
        except Exception:
            pass
 

class ScheduleSection(Vertical):
    def __init__(self, date: datetime) -> None:
        super().__init__()
        self.date = date  

    def compose(self) -> ComposeResult:
        yield Static("Schedule & Tasks", classes="section-header")
        with Horizontal(classes="schedule-controls"):
            yield Button("+ Add Task", id="add-task", classes="schedule-button")
        yield Static("Today's Tasks:", classes="task-header")
        with Vertical(id="tasks-list-day", classes="tasks-list-day"):
            yield Static("No tasks scheduled for today", id="empty-schedule", classes="empty-schedule")

    @on(Button.Pressed, "#add-task")
    async def show_task_form(self, event: Button.Pressed) -> None:
        task_form = TaskForm(self.date)
        task = await self.app.push_screen(task_form)
       
        event.stop()

class NotesSection(Vertical):

    BINDINGS = [
        Binding("ctrl+left", "exit_notes", "Exit Notes", show=True, priority=True),
        Binding("shift+tab", "cycle_focus", "Cycle Focus", show=True),
    ]

    def __init__(self, date: datetime | None = None):
        super().__init__()
        self.date = date
        self.notes_content = "# Notes\nStart writing your notes here..."

    def compose(self) -> ComposeResult:
        yield Static("Notes", classes="section-header")
        with Container(classes="notes-content"):
            yield TextArea(self.notes_content, id="notes-editor")

    def on_key(self, event) -> None:
        if event.key == "ctrl+left" or event.key == "ctrl+right":
            add_task_button = self.app.screen.query_one("#add-task")
            if add_task_button:
                add_task_button.focus()
            event.stop()

    async def action_exit_notes(self) -> None:
        add_task_button = self.app.screen.query_one("#add-task")
        if add_task_button:
            add_task_button.focus()

class DayView(Vertical):

        
    BINDINGS = [
        Binding("up", "move_up", "Previous"),
        Binding("down", "move_down", "Next"),
        Binding("escape", "toggle_menu", "Menu"),
        Binding("ctrl+s", "save_notes", "Save Notes"),
        Binding("left", "move_left", "Left", show=False),
        Binding("right", "move_right", "Right", show=False),
        Binding("enter", "edit_task", "Edit Task"),
    ]

    def __init__(self, date: datetime):
        super().__init__()
        self.date = date
        self.styles.display = "none"

    def compose(self) -> ComposeResult:
        yield Static(f"{self.date.strftime('%B %d, %Y')}", id="day-view-header")
        yield Button("Back to Calendar", id="back-to-calendar", classes="back-button")

        with Horizontal(classes="day-view-content"):
            with Container(classes="schedule-container"):
                yield ScheduleSection(self.date)
            with Horizontal(classes="middle-container"):
                yield Static("Nothing to see here yet", classes="middle-header")
            with Container(classes="notes-container"):
                yield NotesSection(self.date)

    def set_date(self, new_date: datetime) -> None:
        self.date = new_date
        self.query_one("#day-view-header").update(f"{self.date.strftime('%B %d, %Y')}")
        
        schedule_section = self.query_one(ScheduleSection)
        schedule_section.date = new_date
        
        notes_section = self.query_one(NotesSection)
        notes_section.date = new_date
        self.refresh_tasks()
        self.load_notes()
        self.query_one("#add-task").focus()

    def refresh_tasks(self) -> None:
        current_date = self.date.strftime('%Y-%m-%d')
        tasks = self.app.db.get_tasks_for_date(current_date)
        tasks_list = self.query_one("#tasks-list-day")

        tasks_list.remove_children()

        if tasks:
            for task in tasks:
                tasks_list.mount(Task(task))
        else:
            tasks_list.mount(Static("No tasks scheduled for today", classes="empty-schedule"))

    def load_notes(self) -> None:
        notes = self.app.db.get_notes(self.date.strftime('%Y-%m-%d'))
        notes_editor = self.query_one("#notes-editor", TextArea)
        if notes:
            notes_editor.text = notes
        else:
            notes_editor.text = "# Notes\nStart writing your notes here..."

    async def action_move_up(self) -> None:
        current = self.app.focused
        focusable = list(self.query("Button, Task, TextArea"))
        if current in focusable:
            idx = focusable.index(current)
            prev_idx = (idx - 1) % len(focusable)
            focusable[prev_idx].focus()

    async def action_move_down(self) -> None:
        current = self.app.focused
        focusable = list(self.query("Button, Task, TextArea"))
        if current in focusable:
            idx = focusable.index(current)
            next_idx = (idx + 1) % len(focusable)
            focusable[next_idx].focus()

    async def action_edit_task(self) -> None:
        current = self.app.focused
        if isinstance(current, Task):
            task_form = TaskEditForm(current.task_data)
            await self.app.push_screen(task_form)