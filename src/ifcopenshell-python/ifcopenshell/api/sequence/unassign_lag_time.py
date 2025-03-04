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

import ifcopenshell.api


class Usecase:
    def __init__(self, file, **settings):
        self.file = file
        self.settings = {
            "rel_sequence": None,
        }
        for key, value in settings.items():
            self.settings[key] = value

    def execute(self):
        if len(self.file.get_inverse(self.settings["rel_sequence"].TimeLag)) == 1:
            self.file.remove(self.settings["rel_sequence"].TimeLag)
        else:
            self.settings["rel_sequence"].TimeLag = None
        ifcopenshell.api.run(
            "sequence.cascade_schedule",
            self.file,
            task=self.settings["rel_sequence"].RelatedProcess,
        )
