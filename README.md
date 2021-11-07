# Blendshape Groups

An api to expose blendShape groups.

BlendShape groups have absolutely no access point with Maya's existing apis, except from a few obscure mel commands.<br>
Though these mel commands completely rely on Shape Editor selection, making it impractical to write code with it.<br>
This class exposes methods to easily modify and manage a blendShape's groups.

## Installation

Simply put the script where your PYTHON path is pointing to, so that the module ca be imported.

## Supported versions

This tool was tested in Maya 2018 Extension 4.<br>
It was also written to be compatible for both Python 2 and 3, so it should work with Maya 2017 and above.

## Usage

First import the module:<br>
```python
import blendshape_groups
```

Then to test on an example, let's create a poly sphere with a blendShape and some targets:

```python
# Create a poly sphere and add a blendShape to it.
cmds.file(new=True, force=True)
cmds.polySphere(name="sphere")
blendshape = cmds.blendShape("sphere")[0]

# Add a bunch of blendShape targets.
food = {"apple": 0, "banana": 1, "carrot": 2, "durian": 3, "eggplant": 4, "fennel": 5}
for name, index in food.items():
    cmds.blendShape(blendshape, e=True, target=["sphere", index, "sphere", 1])
    cmds.aliasAttr(name, "{bs}.w[{idx}]".format(bs=blendshape, idx=index))
```

Pass the blendShape to the class:
```python
shape_grps = BlendShapeGroups(blendshape)
```

Now we can begin managing the blendShape's groups.<br>
Here's various methods that can be used:

```python
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
```

## Reporting a bug / Requesting a feature

If you run into any bugs or have a request to extend this library, then please <a href='https://github.com/theRussetPotato/blendshape-groups/issues'>create a new issue</a> from this repository.
