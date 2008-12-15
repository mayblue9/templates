import sys

NAMED_CHILD_TYPES = dict.fromkeys(
    ['Timestamp', 'Legend', 'Frame', 'xAxis', 'yAxis', 'altxAxis', 'altyAxis',
     'AxisBar', 'AxisLabel', 'Tick', 'TickLabel', 'Title', 'Subtitle', 'View',
     'World', 'BaseLine', 'Symbol', 'Line', 'Fill', 'AnnotatedValue',
     'ErrorBar']
    )
DYNAMIC_CHILD_TYPES = ['Graph', 'DataSet', 'DrawingObject']

class GraceObject(object):
    """Since most of the classes in PyGrace are basically just dictionaries
    with special string representations and a place to specify defaults for
    attributes, this class does the work that most of the classes need to do.
    The __init__ method just sets all of the parameters passed as the values
    of the attributes.  Also, the __getitem__ method returns a string
    representation of the attribute (with an option to pass a formatting
    command by setting the appropriate value in _formatting_template.

    In addition, the parents and children of each object are recorded, so that
    all objects in a tree can access each other."""
    def __init__(self, parent, attrs, *args, **kwargs):
        
        # set all key, value pairs in attrs to attributes of self
        self._set_kwargs_attributes(attrs)

        # link object to parent, root, and children
        self._link(parent)
                            
        # this dictionary holds any special string formatting commands for each
        # attribute
        self._formatting_template = {}

    def _set_kwargs_attributes(self, attrDict):
        """This sets all of the arguements that are given as default arguments
        as the attributes of the class."""

        # parent gets set in a separate function (and self doesn't need it)
        for reserved in ['self', 'parent']:
            if attrDict.has_key(reserved):
                del attrDict[reserved]

        for key, value in attrDict.iteritems():
            setattr(self, key, value)

        # store default formatting attributes for later use
        for nonformat in ['index', 'data', 'colors']:
            if attrDict.has_key(nonformat):
                del attrDict[nonformat]

        # remove duplicates
        self.defaultAttributes = dict.fromkeys(attrDict.keys())
        
    def _link(self, parent):
        """If there is no parent, set self as root.  Otherwise, record who the
        parent and the root of the tree are.  Also, this records self in the
        list of children of the parent."""

        # store parent in public attribute
        self.parent = parent

        # these hold the children in dictionaries, to avoid duplication.  to
        # access the children, one must call the children() method.
        self._namedChildren = {}
        self._dynamicChildren = {}

        # store root (Grace object) as public attribute for easy access
        if parent is None:
            self.root = self
        else:
            self.root = parent.root

            # if parent can only have one of this type of child, then replace
            # the old child (if one exists) with the new child.
            if self._staticType in NAMED_CHILD_TYPES:
                parent._namedChildren[self._staticType] = self

            # if the type of the child object is one of the dynamic types,
            # then append to a list of like types of children
            elif self._staticType in DYNAMIC_CHILD_TYPES:
                try:
                    parent._dynamicChildren[self._staticType].append(self)
                except KeyError:
                    parent._dynamicChildren[self._staticType] = [self]

            # throw error if _staticType is not in one of lists
            else:
                message = 'unknown _staticType (%s) of %s object' \
                    % (self._staticType, self.__class__.__name__)
                raise TypeError(message)

    def children(self):
        
        # put named children alphabetically first in list
        result = [child for (name, child) 
                  in sorted(self._namedChildren.iteritems())]
        
        # loop through dynamic children types in order
        for childType in DYNAMIC_CHILD_TYPES:
            if self._dynamicChildren.has_key(childType):
                result.extend(self._dynamicChildren[childType])

        return result

    def add_color(self, red, green, blue, name=None):
        """Calls the add_color method of the root of the tree. The method must
        be overwritten by the root to avoid infinite recursion."""
        return self.root.add_color(red, green, blue, name)

    def _check_type(self, allowedTypes, key, value):
        """Throw error if value is not of a type in allowedTypes."""

        # check the type
        correctType = isinstance(value, allowedTypes)

        # format the error message
        if isinstance(allowedTypes, (list, tuple)):
            allowedString = ' or '.join(i.__name__ for i in allowedTypes)
        else:
            allowedString = allowedTypes.__name__

        # throw an informative error if it fails
        if not correctType:
            actualString = type(value).__name__
            message = '%s attribute must be a %s (got %s instead)' % \
                      (key, allowedString, actualString)
            raise TypeError(message)

    def _check_range(self, key, value, min_, max_,
                     includeMin=True, includeMax=True):
        """Throw error if value is not in between min_ and max_."""

        # check for lower bound (and make nice error message if it fails)
        gtString = '>'
        if not min_ == None:
            passMin = False
            if includeMin:
                gtString = '>='
                if value >= min_: passMin = True
            else:
                if value > min_: passMin = True
        else:
            passMin = True
            min_ = '-inf'

        # check for upper bound (and make nice error message if it fails)
        ltString = '<'
        if not max_ == None:
            passMax = False
            if includeMax:
                ltString = '<='
                if value <= max_: passMax = True
            else:
                if value < max_: passMax = True
        else:
            passMax = True
            max_ = '+inf'
            
        # throw an informative error if it fails either one
        if not (passMin and passMax):
            message = '%s does not satisfy %s %s %s %s %s' % \
                      (value, min_, gtString, key, ltString, max_)
            raise ValueError(message)

    def _check_membership(self, key, value, set):
        """Throw an error if value is not in set (set can be any container with
        a __contains__ method defined."""

        # check if the value is in the set of allowed values
        passTest = value in set

        # throw an error message that notifies user of allowed values
        if not passTest:
            message = '%s = %s is not in %s' % (key, value, set)
            raise ValueError(message)

    def __setattr__(self, key, value):

        # this list of checks on the type and value is not complete (FIX)
        if key.endswith('linestyle'):
            self._check_type((int,), key, value)
            self._check_range(key, value, 0, 8)
        elif key.endswith('linewidth'):
            self._check_type((float, int), key, value)
            self._check_range(key, value, 0, None)
        elif key.endswith('just'):
            self._check_type((int,), key, value)
            self._check_range(key, value, 0, 12, includeMax=False)
        elif key.endswith('size'):
            self._check_type((float, int), key, value)
            self._check_range(key, value, 0, None)
        elif key == 'x' or key == 'y':
            self._check_type((float, int), key, value)
        elif key == 'xmin' or key == 'xmax' or key == 'ymin' or key == 'ymax':
            self._check_type((float, int), key, value)
        elif key == 'onoff':
            self._check_type((str,), key, value)
        elif key == 'hidden':
            self._check_type((str,), key, value)
        elif key == 'rot':
            self._check_type((float, int), key, value)
        elif key == 'length': # legend line length
            self._check_type((int,), key, value)
            self._check_range(key, value, 0, 8, includeMax=True)
        elif key.endswith('pattern'):
            self._check_type((int,), key, value)
            self._check_range(key, value, 0, 32, includeMax=False)
        elif key.endswith('_tup'):
            self._check_type(tuple, key, value)
        elif key == 'upright' or key == 'lowleft':
            self._check_type(tuple, key, value)
        elif key == 'loctype':
            self._check_type(str, key, value)
            self._check_membership(key, value, ('world', 'view'))
        elif key.endswith('_loc'):
            self._check_type(str, key, value)
            self._check_membership(key, value, ('auto', 'spec', 'para'))
        elif key == 'onoff':
            self._check_type(str, key, value)
            self._check_membership(key, value, ('on', 'off'))
        elif key == 'text':
            self._check_type(str, key, value)
        elif key == 'format':
            self._check_type(str, key, value)
            FORMAT_TYPES = ('general', 'decimal', 'power')
            upperTypes = [t.upper() for t in FORMAT_TYPES]
            self._check_membership(key, value.upper(), upperTypes)
        elif key == 'prec':
            self._check_type(int, key, value)
            self._check_range(key, value, 0, 9)
        elif key == 'append' or key == 'prepend':
            self._check_type(str, key, value)
        elif key == 'offset':
            self._check_type(tuple, key, value)
        elif key == 'place':
            self._check_type(str, key, value)
            self._check_membership(key, value, ('normal', 'opposite', 'both'))
            
        # actually set the value of the attribute here
        object.__setattr__(self, key, value)
        
    def __getitem__(self, key):
        """Always returns a formatted string representation of an attribute
        by checking in self._formatting_template"""

        # look up fonts and colors in root object
        if key.endswith('color'):
            return self._format_color(getattr(self, key))
        elif key.endswith('font'):
            return self._format_font(getattr(self, key))

        # try to lookup special formatting command in _formatting_template
        try:
            return self._formatting_template[key] % getattr(self, key)
        # if there isn't one, just convert to a string
        except KeyError:
            return str(getattr(self, key))

    def __eq__(self,other):
        """Two objects are the same if all of their attributes are the same.
        Otherwise they are not the same.
        """

        # throw error if the objects are not of the same type
        if not isinstance(other,self.__class__):
            message = "can't compare equality of different type (%s != %s)" % \
                      (type(self), type(other))
            raise TypeError(message)

        # compare all of the default attributes of the two objects
        for attr in self.defaultAttributes:
            if getattr(self,attr)!=getattr(other,attr):
                return False
        return True

    def __ne__(self,other):
        """Two objects are the same if all of their attributes are the same.
        Otherwise they are not the same.
        """
        return not self.__eq__(other)

    def _format_font(self, value):
        """Throw error if font is not defined, otherwise return string
        representation of font (either integer or quoted string)"""
        try:
            return self.root.fonts[value]
        except KeyError:
            message = "'%s' font is not defined" % value
            raise KeyError(message)
            
    def _format_color(self, value):
        """Throw error if color is not defined, otherwise return string
        representation of color (either integer or quoted string)"""
        try:
            return self.root.colors[value]
        except KeyError:
            message = "'%s' color is not defined" % value
            raise KeyError(message)

    def configure(self, **kwargs):
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)

    def configure_group(self, *args, **kwargs):
        for arg in args:
            for attr, value in kwargs.iteritems():
                setattr(arg, attr, value)

    def scale_suffix(self, value, suffix, all=True):
        """Scale all attributes with name ending in 'suffix' to value times the
        original value.  If 'all' is True, then same is set for all children
        recursively too."""

        # set all attributes ending in suffix to value
        attrList = [(getattr(self, name), name) for name in dir(self)]
        for attr, name in attrList:
            if not callable(attr) and name.endswith(suffix):
                oldValue = getattr(self, name)
                setattr(self, name, oldValue * value)

        # if the 'all' flag is true, do the same for all children
        if all:
            for child in self.children():
                child.scale_suffix(value, suffix, all)

    def set_suffix(self, value, suffix, all=True):
        """Set all attributes with name ending in 'suffix' to value.  If 'all'
        is True, then same is set for all children recursively too."""

        # set all attributes ending in suffix to value
        attrList = [(getattr(self, name), name) for name in dir(self)]
        for attr, name in attrList:
            if not callable(attr) and name.endswith(suffix):
                setattr(self, name, value)

        # if the 'all' flag is true, do the same for all children
        if all:
            for child in self.children():
                child.set_suffix(value, suffix, all)

    def set_fonts(self, font, all=True):
        """Set all fonts to given value.  Recursive if 'all' is True."""
        self.set_suffix(font, 'font', all)

    def set_colors(self, color, all=False):
        """Set all colors to given value.  Recursive if 'all' is True."""
        self.set_suffix(color, 'color', all)

    def set_linewidths(self, width, all=True):
        """Set all linewidths to given value.  Recursive if 'all' is True."""
        self.set_suffix(width, 'linewidth', all)

    def set_data_linewidths(self, width, all=True):
        """Set all linewidths for datasets to given value.  Recursive if
        'all' is True."""
        try:
            for dataset in self.datasets:
                dataset.set_suffix(width, 'linewidth', all)
        except AttributeError:
            pass

    def copy_format(self, other, all=True):

        # other is a class, not an instance of a class
        if isinstance(other,type):
            
            complete = False
            args = []
            while not complete:
                try:
                    x = other(*args)
                except TypeError:
                    args.append(None)
                else:
                    complete = True
#            print type(x),x.__class__,x.xaxis.tick.major_size
#            print type(x.xaxis)
            self.copy_format(x, all=all)
            
        # other is an instance of a class
        else:
            try:
                a = other.xaxis.tick.major_size
                b = type(other.xaxis)
#                print 'major_size', a, b
            except:
                pass


##             # throw error if the objects are not of the same type
##             if not isinstance(other,self.__class__):
##                 message = "can't copy format of different type (%s != %s)" % \
##                           (type(self), type(other))
##                 raise TypeError(message)

            # set all default attibutes to the same values as other
            for attr in self.defaultAttributes:
#                print type(other), attr, getattr(other, attr)
                setattr(self, attr, getattr(other, attr))

#            print type(self), map(type, self.children)
#            print type(other), map(type, other.children)
            if all:
                for thisChild, thatChild in zip(self.children(), other.children()):
#                    print 'children', type(thisChild), type(thatChild)
                    thisChild.copy_format(thatChild)

class BaseSet(object):
    """This is a container class that stores objects by name and index.  This
    is meant to be subclassed."""
    def __init__(self, items):

        # store items and index
        self.items = items
        self._index = len(items)

        # for quick lookup, store mappings
        self.name2item = {}
        self.index2item = {}
        for item in self.items:
            self.name2item[item.name] = item
            self.index2item[item.index] = item

    def __contains__(self, value):
        """Returns true if either integer index or string value is in."""
        if isinstance(value, str):
            return value in self.name2item
        elif isinstance(value, int):
            return value in self.index2item
        else:
            return False

    def __str__(self):
        """Returns the string representation of each item in the set (sorted
        by index and separated by newlines)."""
        sorted = [(item.index, item) for item in self.items]
        sorted.sort()
        return '\n'.join(str(item) for index, item in sorted)

    # iterate over items (objects that is, not index or name)
    def __len__(self): return len(self.items)
    def __iter__(self): return iter(self.items)

    def __getitem__(self, value):
        """Allow retreival by index or name.  Error is thrown if neither index
        or name is in the set."""
        if value in self:
            if isinstance(value, str):
                return '"%s"' % value
            elif isinstance(value, int):
                return str(value)
        else:
            message = str(value)
            raise KeyError(message)

    def add_item(self, ItemClass, *args, **kwargs):
        item = ItemClass(self._index, *args, **kwargs)
        self.items.append(item)
        self._index += 1
        self.name2item[item.name] = item
        self.index2item[item.index] = item
        return item    

    def get_item_by_index(self, index):
        try:
            return self.index2item[index]
        except KeyError:
            message = "'%i' is not a valid index" % index
            raise KeyError(message)

    def get_item_by_name(self, name):
        try:
            return self.name2item[name]
        except KeyError:
            message = "'%s' is not a valid name" % name
            raise KeyError(message)