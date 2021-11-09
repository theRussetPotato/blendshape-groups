"""
A simple library to expose blendShape groups.

BlendShape groups have absolutely no access point with Maya's existing apis, except from a few obscure mel commands.
Though these mel commands completely rely on Shape Editor selection, making it impractical to write code with it.
This library exposes methods to easily modify and manage a blendShape's groups.

Author:
    Jason Labbe
    https://github.com/theRussetPotato/blendshape-groups

Usage example:
    import blendshape_groups
    blendshape_groups.create_example_scene()  # Check out function for full detail usage.
"""

import maya.cmds as cmds
import maya.mel as mel


class BlendShapeGroups(object):

    def __init__(self, blendshape):
        self._blendshape = blendshape

    def __iter__(self):
        for grp_index in self._grp_iterator():
            yield grp_index

    def _extract_index(self, attr):
        """Extracts an index from a attribute string representing an array."""
        return int(attr.split("[")[1].rstrip("]"))

    def _next_grp_index(self):
        """Fetches the next available group index for creation."""
        return mel.eval("blendShapeUnusedTargetDirectoryIndex {};".format(self._blendshape))

    def _get_grp_parent(self, grp_index):
        """Gets the supplied group's current parent index."""
        return cmds.getAttr("{}.targetDirectory[{}].parentIndex".format(self._blendshape, grp_index))

    def _set_grp_parent(self, grp_index, parent_grp_index):
        """Sets the supplied group's to be parented under a new index."""
        cmds.setAttr("{}.targetDirectory[{}].parentIndex".format(self._blendshape, grp_index), parent_grp_index)

    def _get_grp_children(self, grp_index):
        """Gets a list of indices (groups and targets) of the supplied group.
        Groups are listed as negative numbers.
        """
        return cmds.getAttr("{}.targetDirectory[{}].childIndices".format(self._blendshape, grp_index)) or []

    def _set_grp_children(self, grp_index, indices):
        """Replaces supplied group's children with a list of indices representing other groups and targets.
        Groups are listed as negative numbers.
        """
        cmds.setAttr("{}.targetDirectory[{}].childIndices".format(self._blendshape, grp_index), indices, type="Int32Array")

    def _grp_exists(self, index):
        """Checks if the group at the supplied index is valid."""
        attrs = cmds.listAttr("{}.targetDirectory".format(self._blendshape), multi=True) or []
        grp_attr = "targetDirectory[{}]".format(index)
        return grp_attr in attrs

    def _check_grp_validation(self, grp_index):
        if not self._grp_exists(grp_index):
            raise ValueError("Group index {} isn't valid because it doesn't exist".format(grp_index))

    def _build_unique_name(self, grp_index, name):
        """Generates a unique name if the supplied name will cause a conflict with another group."""
        parent_children = self._get_grp_children(grp_index)

        existing_names = [
            cmds.getAttr("{}.targetDirectory[{}].directoryName".format(self._blendshape, -index))
            for index in parent_children
            if index < 0
        ]

        num = 1
        new_name = name
        while new_name in existing_names:
            new_name = "{}{}".format(name, num)
            num += 1

        return new_name

    def _grp_iterator(self):
        """An iterator to go through all groups with a for loop."""
        for attr in cmds.listAttr("{}.targetDirectory".format(self._blendshape), multi=True) or []:
            if len(attr.split(".")) == 1:
                yield self._extract_index(attr)

    def _grp_parent_iterator(self, grp_index):
        """An iterator that steps through a group's hierarchy by going up its parents."""
        parent_index = self._get_grp_parent(grp_index)
        if parent_index > 0:
            yield parent_index

            for result in self._grp_parent_iterator(parent_index):
                yield result

    def get_all_grp_indices(self):
        """Fetches a list of all available group indices."""
        return list(self._grp_iterator())

    def get_grp_indices(self, grp_index):
        """Fetches a list of group indices that are parented to the supplied group (excludes nested groups)."""
        self._check_grp_validation(grp_index)

        return [
            int(-index)
            for index in self._get_grp_children(grp_index)
            if index < 0
        ]

    def get_grp_count(self):
        """Returns the current number of groups. Root group is included in the count."""
        return len(self.get_all_grp_indices())

    def move_grps(self, indices, grp_index):
        """Moves multiple groups to be parented under a new group.

        Args:
            indices: A list of indices representing groups to be moved.
            grp_index: An index representing a group to parent to.
        """
        self._check_grp_validation(grp_index)

        conflict_indices = list(self._grp_parent_iterator(grp_index))

        for index in reversed(indices):
            if index == grp_index:
                indices.pop(indices.index(index))
                cmds.warning("Unable to move group index {} to itself".format(index))
                continue

            if index in conflict_indices:
                indices.pop(indices.index(index))
                cmds.warning("Unable to move to group index {} to one of its own children".format(index))

        for index in indices:
            old_parent_index = self._get_grp_parent(index)
            parent_child_indices = self._get_grp_children(old_parent_index)
            if -index in parent_child_indices:
                parent_child_indices.pop(parent_child_indices.index(-index))

            self._set_grp_children(old_parent_index, parent_child_indices)

        child_indices = self._get_grp_children(grp_index)
        for index in indices:
            if -index not in child_indices:
                child_indices.append(-index)
            self._set_grp_parent(index, grp_index)

        self._set_grp_children(grp_index, child_indices)

    def move_targets(self, indices, grp_index):
        """Moves targets to be parented under a new group.

        Args:
            indices: A list of indexes representing targets to be moved.
            grp_index: An index representing the group to be moved to.
        """
        self._check_grp_validation(grp_index)

        child_indices = self._get_grp_children(grp_index)
        for index in indices:
            if index not in child_indices:
                child_indices.append(index)

            old_parent_index = cmds.getAttr("{}.parentDirectory[{}]".format(self._blendshape, index))
            parent_child_indices = self._get_grp_children(old_parent_index)
            if index in parent_child_indices:
                parent_child_indices.pop(parent_child_indices.index(index))
                self._set_grp_children(old_parent_index, parent_child_indices)

            cmds.setAttr("{}.parentDirectory[{}]".format(self._blendshape, index), grp_index)

        self._set_grp_children(grp_index, child_indices)

    def rename_grp(self, grp_index, name):
        """Renames the supplied group. Names with conflicts will be auto-named.

        Args:
            grp_index: An index representing a group to rename.
            name: What to rename the group to.

        Returns:
            The new name of the group (in case it was renamed).
        """
        self._check_grp_validation(grp_index)

        parent_index = self._get_grp_parent(grp_index)
        new_name = self._build_unique_name(parent_index, name)
        cmds.setAttr("{}.targetDirectory[{}].directoryName".format(self._blendshape, grp_index), new_name, type="string")
        return new_name

    def get_grp_name(self, grp_index):
        """Returns the supplied group's name."""
        self._check_grp_validation(grp_index)
        return cmds.getAttr("{}.targetDirectory[{}].directoryName".format(self._blendshape, grp_index))

    def create_grp(self, parent_grp_index=0, targets=[], name="New Group"):
        """Creates a new group and parents targets under it.

        Args:
            parent_grp_index: An index representing which group to parent this new group to.
            targets: A list of target indices to parent under the new group. Make this an empty list to create an empty group.
            name: What to name the new group.

        Returns:
            The index of the new group.
        """
        new_grp_index = self._next_grp_index()
        self.move_grps([new_grp_index], parent_grp_index)
        self._set_grp_parent(new_grp_index, parent_grp_index)
        self.rename_grp(new_grp_index, name)
        self.move_targets(targets, new_grp_index)
        return new_grp_index

    def delete_grp(self, grp_index):
        """Deletes the supplied group and anything parented underneath it.
        Undo will not reflect in the Shape Editor until it is reopened.
        """
        self._check_grp_validation(grp_index)

        parent_grp_index = self._get_grp_parent(grp_index)
        parent_grp_children = self._get_grp_children(parent_grp_index)
        if -grp_index in parent_grp_children:
            parent_grp_children.pop(parent_grp_children.index(-grp_index))
            self._set_grp_children(parent_grp_index, parent_grp_children)

        children_indices = self._get_grp_children(grp_index)
        for index in children_indices:
            if index < 0:
                self.delete_grp(-index)
            else:
                self.delete_target(index)

        cmds.removeMultiInstance("{}.targetDirectory[{}]".format(self._blendshape, grp_index), b=True)

    def get_all_target_indices(self):
        """Fetches a list of valid target indices."""
        return [
            self._extract_index(attr)
            for attr in cmds.listAttr("{}.parentDirectory".format(self._blendshape), multi=True) or []
        ]

    def get_grp_target_indices(self, grp_index):
        """Fetches a list of valid target indices that are parented to the supplied group (excludes nested targets)."""
        self._check_grp_validation(grp_index)

        return [
            int(index)
            for index in self._get_grp_children(grp_index)
            if index >= 0
        ]

    def find_grp(self, grp_name):
        """Searches groups and returns its index if it matches the supplied name.
        Returns None if nothing is found.
        """
        for grp_index in self:
            if grp_name == self.get_grp_name(grp_index):
                return grp_index

    def delete_target(self, index):
        """Deletes a target at the supplied index."""
        mel.eval("blendShapeDeleteTargetGroup {} {};".format(self._blendshape, index))


def create_example_scene():
    # Create a poly sphere and add a blendShape to it.
    cmds.file(new=True, force=True)
    cmds.polySphere(name="sphere")
    blendshape = cmds.blendShape("sphere")[0]

    # Add a bunch of blendShape targets.
    food = {"apple": 0, "banana": 1, "carrot": 2, "durian": 3, "eggplant": 4, "fennel": 5}
    for name, index in food.items():
        cmds.blendShape(blendshape, e=True, target=["sphere", index, "sphere", 1])
        cmds.aliasAttr(name, "{bs}.w[{idx}]".format(bs=blendshape, idx=index))

    # Pass blendShape to class to modify its groups.
    shape_grps = BlendShapeGroups(blendshape)

    # Create an empty group called 'Market'.
    market_index = shape_grps.create_grp(name="Market")

    # Create a group called 'Fruit' with a bunch of targets, and parent it under 'Market' group.
    shape_grps.create_grp(
        name="Fruit", targets=[food["apple"], food["banana"], food["durian"]], parent_grp_index=market_index)

    # Create another empty group called 'Veggies'.
    veggies_index = shape_grps.create_grp(name="Veggies")

    # Add targets to 'Veggies' group.
    shape_grps.move_targets([food["carrot"], food["eggplant"], food["fennel"]], veggies_index)

    # Move 'Veggies' group under 'Market' group.
    shape_grps.move_grps([veggies_index], market_index)

    # Print a list of all available group indices.
    # Output: [0, 1, 2, 3]
    print(shape_grps.get_all_grp_indices())

    # Print a list of all group indices parented under 'Market' group.
    # Output: [2, 3]
    print(shape_grps.get_grp_indices(market_index))

    # Print the number of available groups.
    # Output: 4
    print(shape_grps.get_grp_count())

    # Print a list of target indices from all groups.
    # Output: [0, 1, 2, 3, 4, 5]
    print(shape_grps.get_all_target_indices())

    # Print a list of target indices from 'Veggies' group.
    # Output: [2, 4, 5]
    print(shape_grps.get_grp_target_indices(veggies_index))

    # Iterate over all groups.
    for grp_index in shape_grps:
        grp_name = shape_grps.get_grp_name(grp_index)
        print(grp_index, grp_name)
        # Output:
        # 0 Group
        # 1 Market
        # 2 Fruit
        # 3 Veggies

    # Rename 'Market' group to 'Fruit Market'
    shape_grps.rename_grp(1, "Fruit Market")

    # Delete 'Veggies' group including all of its targets.
    shape_grps.delete_grp(veggies_index)

    # Delete 'banana' target by using its index.
    shape_grps.delete_target(food["banana"])
