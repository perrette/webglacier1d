""" Controls which forms are accessible
"""
from wtforms import widgets
from wtforms import RadioField, SelectMultipleField, TextField, IntegerField, SelectField, TextAreaField, SubmitField, HiddenField, Field, FormField, FloatField, Form as WtForm, BooleanField
from wtforms.validators import ValidationError, Required, Regexp, NumberRange
from flask.ext.wtf import Form

import config as o

from models.greenmap import get_coords
c = get_coords(o.glacier_default)

# for check-box like selectmultiplefield
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class MapCoordinates(WtForm):
    # coordinate box to directly enter coordinates
    pass


class MapForm(Form):

    # drop-down list to select dataset
    dataset = SelectField("Dataset", choices=[(d,d.capitalize()) for d in o.dataset_choices], default=o.dataset_default)

    # drop-down list to select glacier
    glacier = SelectField("Glacier", choices=[(d,d.capitalize()) for d in o.glacier_choices], default=o.glacier_default)

    #coords = FormField(MapCoordinates()) 
    left = FloatField(default=c[0])
    right = FloatField(default=c[1])
    bottom = FloatField(default=c[2])
    top = FloatField(default=c[3])
    #submit = SubmitField()

class FlowLineForm(Form):
    maxdist = FloatField('Flowline Max Length (km)', default=o.maxdist)
    dx = FloatField('Step (km)',default=o.dx)
    x = FloatField(validators=[Required()])
    y = FloatField(validators=[Required()])
    # resample = IntegerField(default=o.resample)
    dataset = SelectField("Velocity Dataset", 
                          choices=[(d, d.capitalize()) for d in o.sources_choices['velocity_mag']],
                          default=o.sources_default['velocity_mag'])

class ExtractForm(Form):
    # variables = MultiCheckboxField('Extract Variables:', 
    # variables = SelectMultipleField('Extract Variables:', 
            # choices=[(v,v) for v in o.variables_choices],
            # default=[v for v in o.variables_default])

    for v in o.variables:
        # locals()[v] = BooleanField(default=True)
        locals()[v] = SelectField(
            choices=[(d,d) for d in o.sources_choices[v]],
            default=o.sources_default[v]
        )

class MeshForm(Form):
    dx = FloatField('x grid step (m)',default=o.mesh_dx)
    ny = FloatField('number of cross-flow points',default=o.mesh_ny)
