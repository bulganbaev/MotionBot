class Falgs:

    def __init__(self):

        self.flags = {}
        self.no_parents = []

    def get_flags(self):
        """
        return all the flags
        :return:
        """
        return self.flags.keys()

    def add_flag(self, name, default, parents):
        """
        Add a flag to the dictionary
        :param name: the name of the flag
        :param default: its default value
        :param parents: a list of parents
        :return:
        """

        # check if the name is part of the flag list
        if name in self.get_flags():
            raise KeyError(f"Key '{name}' already in dictionary")

        # check if the parents are in the flag list
        for p in parents:
            if p not in self.get_flags():
                raise KeyError(f"Parent '{p}' not in dictionary for key '{name}'")

        # check if the value is bool
        if not isinstance(default, bool):
            raise ValueError("Default must be bool")

        # add the isntance to the list
        self.flags[name] = {
            'value': default,
            'childrens': [],
            'parents': []
        }

        # add its parents
        self.flags[name]['parents'] = parents

        # add the current flag to the no parents one
        if len(parents) == 0:
            self.no_parents.append(name)

        # compute children
        self.compute_children()

    def flip_value(self, name):
        """
        Flip the value of a certain flags
        :param name: (str) the name of the flag
        :return:
        """

        # check for the name in the list of flags
        if name not in self.get_flags():
            raise KeyError(f"Key {name} not in dictionary")

        # get the current value
        value = self.get_value(name)

        # set it to the new value
        self.set_value(name, not value)

    def compute_children(self):
        """
        Add the children to the linked dictionary
        :return:
        """

        # for every entry in the flag dict
        for entry in self.get_flags():

            # for every parent to that entry
            for p in self.flags[entry]['parents']:

                # if the parend doesn't have the entry in its children list
                if not entry in self.flags[p]['childrens']:
                    # append it
                    self.flags[p]['childrens'].append(entry)

    def set_value(self, name, value):
        """
        Set the value of a flag recursively
        :param name: the name of the falg
        :param value: the value (bool)
        :return:
        """

        if name not in self.get_flags():
            raise KeyError(f"Flag {name} not found")

        if not isinstance(value, bool):
            raise ValueError(f"{value} is not bool")

        # if the value is false
        if not value:
            # set all the childrens to false
            for ch in self.flags[name]['childrens']:
                self.set_value(ch, False)

        self.flags[name]['value'] = value

    def get_value(self, name):
        """
        Return the value of a flag
        :param name: (str) the name of the flag
        :return:
        """

        if name not in self.get_flags():
            raise KeyError(f"Flag {name} not found")

        return self.flags[name]['value']

    def check_consistency(self):
        """
        Check the consistency of the flags, if a parent is false all its children must be false
        :return:
        """

        checked = []

        for entry in self.no_parents:

            if not self.get_value(entry):
                for child in self.flags[entry]['childrens']:
                    self.set_value(child, False)

            checked.append(entry)

        for entry in self.get_flags():
            if entry in checked: continue

            if not self.get_value(entry):
                for child in self.flags[entry]['childrens']:
                    self.set_value(child, False)
