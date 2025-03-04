# IfcOpenShell - IFC toolkit and geometry engine
# Copyright (C) 2021 Dion Moult <dion@thinkmoult.com>
#
# This file is part of IfcOpenShell.
#
# IfcOpenShell is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IfcOpenShell is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with IfcOpenShell.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import ifcopenshell.util.date
import ifcopenshell.util.sequence


class Usecase:
    def __init__(self, file, **settings):
        self.file = file
        self.settings = {"task_time": None, "attributes": {}}
        for key, value in settings.items():
            self.settings[key] = value

    def execute(self):
        self.task = self.get_task()
        self.calendar = ifcopenshell.util.sequence.derive_calendar(self.task)

        # If the user specifies both an end date and a duration, the duration takes priority
        if (
            self.settings["attributes"].get("ScheduleDuration", None)
            and "ScheduleFinish" in self.settings["attributes"].keys()
        ):
            del self.settings["attributes"]["ScheduleFinish"]

        duration_type = self.settings["attributes"].get(
            "DurationType", self.settings["task_time"].DurationType
        )
        finish = self.settings["attributes"].get("ScheduleFinish", None)
        if finish:
            if isinstance(finish, str):
                finish = datetime.datetime.fromisoformat(finish)
            self.settings["attributes"]["ScheduleFinish"] = datetime.datetime.combine(
                ifcopenshell.util.sequence.get_soonest_working_day(
                    finish, duration_type, self.calendar
                ),
                datetime.time(17),
            )
        start = self.settings["attributes"].get("ScheduleStart", None)
        if start:
            if isinstance(start, str):
                start = datetime.datetime.fromisoformat(start)
            self.settings["attributes"]["ScheduleStart"] = datetime.datetime.combine(
                ifcopenshell.util.sequence.get_soonest_working_day(
                    start, duration_type, self.calendar
                ),
                datetime.time(9),
            )

        for name, value in self.settings["attributes"].items():
            if value is not None:
                if "Start" in name or "Finish" in name or name == "StatusTime":
                    value = ifcopenshell.util.date.datetime2ifc(value, "IfcDateTime")
                elif (
                    name == "ScheduleDuration"
                    or name == "ActualDuration"
                    or name == "RemainingTime"
                ):
                    value = ifcopenshell.util.date.datetime2ifc(value, "IfcDuration")
            setattr(self.settings["task_time"], name, value)

        if (
            "ScheduleDuration" in self.settings["attributes"].keys()
            and self.settings["task_time"].ScheduleDuration
            and self.settings["task_time"].ScheduleStart
        ):
            self.calculate_finish()
        elif (
            self.settings["attributes"].get("ScheduleStart", None)
            and self.settings["task_time"].ScheduleDuration
        ):
            self.calculate_finish()
        elif (
            self.settings["attributes"].get("ScheduleFinish", None)
            and self.settings["task_time"].ScheduleStart
        ):
            self.calculate_duration()

        if self.settings["task_time"].ScheduleDuration and (
            "ScheduleStart" in self.settings["attributes"].keys()
            or "ScheduleFinish" in self.settings["attributes"].keys()
            or "ScheduleDuration" in self.settings["attributes"].keys()
        ):
            ifcopenshell.api.run("sequence.cascade_schedule", self.file, task=self.task)

    def calculate_finish(self):
        finish = ifcopenshell.util.sequence.get_start_or_finish_date(
            ifcopenshell.util.date.ifc2datetime(
                self.settings["task_time"].ScheduleStart
            ),
            ifcopenshell.util.date.ifc2datetime(
                self.settings["task_time"].ScheduleDuration
            ),
            self.settings["task_time"].DurationType,
            self.calendar,
            date_type="FINISH",
        )
        self.settings["task_time"].ScheduleFinish = ifcopenshell.util.date.datetime2ifc(
            finish, "IfcDateTime"
        )

    def calculate_duration(self):
        start = ifcopenshell.util.date.ifc2datetime(
            self.settings["task_time"].ScheduleStart
        )
        finish = ifcopenshell.util.date.ifc2datetime(
            self.settings["task_time"].ScheduleFinish
        )
        current_date = datetime.date(start.year, start.month, start.day)
        finish_date = datetime.date(finish.year, finish.month, finish.day)
        duration = datetime.timedelta(days=1)
        while current_date < finish_date:
            if (
                self.settings["task_time"].DurationType == "ELAPSEDTIME"
                or not self.calendar
            ):
                duration += datetime.timedelta(days=1)
            elif ifcopenshell.util.sequence.is_working_day(current_date, self.calendar):
                duration += datetime.timedelta(days=1)
            current_date += datetime.timedelta(days=1)
        self.settings[
            "task_time"
        ].ScheduleDuration = ifcopenshell.util.date.datetime2ifc(
            duration, "IfcDuration"
        )

    def get_task(self):
        return [
            e
            for e in self.file.get_inverse(self.settings["task_time"])
            if e.is_a("IfcTask")
        ][0]
