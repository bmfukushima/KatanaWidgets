# Constraint SuperTool
The **Constraint SuperTool** is meant to be an all in one place for setting up constraints
inside of Katana.  This widget will combine all of the constraints into one uber constraint
node which will have three main parameters **Constraint Type, Stack Order, Maintain Offset,
and Constraint Params**.

# Parameters
### Constraint Type
What type of constraint is going to be used.  When this is changed, there is a **Constraint Node**
that is located in the tool which will be swapped out for one of the new type selected.

### Stack Order
Determines the stack order of the constraint.  The stack order is the order in which the 
transforms will be resolved.  If this is set to first, the constraint will be resolved
first, and then the rest of the transforms will be resolved.  If this is set to last, then
all of the transforms will be resolved, and then the constraint will be resolved.

### Maintain Offset
Determines if the offset of the object should be maintained during the constraint.  Often
times a user wants to constraint a location to another location, however they don't want it
to override their current transforms.  This will keep the object in the same position in space,
rotation, scale, etc, while constraining any further manipulations to the target object.

### Constraint Parameters
This is a teledrop parameters, that will automatically update to the constraint node when
the **Constraint Type** is changed.

# Notes
* ParentChildConstraint
  * override to flip the stack order.  As for some reason this stack order is coming in reversed...
* Maintain offset
  * Parent child constraint