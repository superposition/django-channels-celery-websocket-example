You can use the find command 'github' to skip through each example





https://gist.github.com/alixedi/9d4be3e3a274490946df



# Custom range django-filters


custom_range_filters.py
from django import forms

from django_filters.filterset import FilterSet
from django_filters.widgets import RangeWidget
from django_filters.filters import Filter, RangeFilter


class CustomMultiValueField(forms.MultiValueField):ou 
    widget = RangeWidget

    def compress(self, data_list):
        if data_list:
            return slice(*data_list)
        return None


class CustomDateRangeField(CustomMultiValueField):
    def __init__(self, *args, **kwargs):
        fields = (
            forms.DateField(), 
            forms.DateField(),
        )
        super(DateRangeField, self).__init__(fields, *args, **kwargs)



class CustomTimeRangeField(CustomMultiValueField):
    def __init__(self, *args, **kwargs):
        fields = (
            forms.TimeField(),
            forms.TimeField(),
        )
        super(TimeRangeField, self).__init__(fields, *args, **kwargs)


class CustomDateTimeRangeField(CustomMultiValueField):
    def __init__(self, *args, **kwargs):
        fields = (
            forms.DateTimeField(),
            forms.DateTimeField(),
        )
        super(DateTimeRangeField, self).__init__(fields, *args, **kwargs)


class CustomRangeFilter(Filter):
    def filter(self, qs, value):
        if value:
            lookup = '%s__range' % self.name
            return qs.filter(**{lookup: (value.start, value.stop)})
        return qs


class CustomDateRangeFilter(CustomRangeFilter):
    field_class = DateRangeField


class CustomTimeRangeFilter(CustomRangeFilter):
    field_class = TimeRangeField


class CustomDateTimeRangeFilter(CustomRangeFilter):
field_class = DateTimeRangeField
_________________________________________________________________________________

https://gist.github.com/jhgaylor/5873301



 through_relationships.py
class A(models.Model):
    things = models.ManyToManyField("B", through=ThroughModel)

class B(models.Model):
    text = models.TextField()

class ThroughModel(models.Model):
    a = models.ForeignKey(A)
    b = models.ForeignKey(B)
    extra = models.BooleanField()

#this will return a list of ThroughModel objects
ThroughModel.objects.filter(b=instance_of_b, extra=True)

#this will return a list of A objects based on an extra field on the through table
A.objects.filter(things__ThroughModel__extra=True)

#keep in mind that limiting by one of the foreign keys on the through model is easier
A.objects.filter(things=instance_of_b)


_________________________________________________________________________________

https://github.com/carltongibson/django-filter/blob/master/django_filters/fields.py





from collections import namedtuple
from datetime import datetime, time

from django import forms
from django.utils.dateparse import parse_datetime
from django.utils.encoding import force_str
from django.utils.translation import ugettext_lazy as _

from .conf import settings
from .utils import handle_timezone
from .widgets import (
    BaseCSVWidget,
    CSVWidget,
    DateRangeWidget,
    LookupTypeWidget,
    RangeWidget
)


class RangeField(forms.MultiValueField):
    widget = RangeWidget

    def __init__(self, fields=None, *args, **kwargs):
        if fields is None:
            fields = (
                forms.DecimalField(),
                forms.DecimalField())
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            return slice(*data_list)
        return None


class DateRangeField(RangeField):
    widget = DateRangeWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.DateField(),
            forms.DateField())
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            start_date, stop_date = data_list
            if start_date:
                start_date = handle_timezone(
                    datetime.combine(start_date, time.min),
                    False
                )
            if stop_date:
                stop_date = handle_timezone(
                    datetime.combine(stop_date, time.max),
                    False
                )
            return slice(start_date, stop_date)
        return None


class DateTimeRangeField(RangeField):
    widget = DateRangeWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.DateTimeField(),
            forms.DateTimeField())
        super().__init__(fields, *args, **kwargs)


class TimeRangeField(RangeField):
    widget = DateRangeWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.TimeField(),
            forms.TimeField())
        super().__init__(fields, *args, **kwargs)


class Lookup(namedtuple('Lookup', ('value', 'lookup_type'))):
    # python nature is test __len__ on tuple types for boolean check
    def __len__(self):
        if not self.value:
            return 0
        return 2


class LookupTypeField(forms.MultiValueField):
    def __init__(self, field, lookup_choices, *args, **kwargs):
        fields = (
            field,
            forms.ChoiceField(choices=lookup_choices)
        )
        defaults = {
            'widgets': [f.widget for f in fields],
        }
        widget = LookupTypeWidget(**defaults)
        kwargs['widget'] = widget
        kwargs['help_text'] = field.help_text
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if len(data_list) == 2:
            return Lookup(value=data_list[0], lookup_type=data_list[1] or 'exact')
        return Lookup(value=None, lookup_type='exact')


class IsoDateTimeField(forms.DateTimeField):
    """
    Supports 'iso-8601' date format too which is out the scope of
    the ``datetime.strptime`` standard library
    # ISO 8601: ``http://www.w3.org/TR/NOTE-datetime``
    Based on Gist example by David Medina https://gist.github.com/copitux/5773821
    """
    ISO_8601 = 'iso-8601'
    input_formats = [ISO_8601]

    def strptime(self, value, format):
        value = force_str(value)

        if format == self.ISO_8601:
            parsed = parse_datetime(value)
            if parsed is None:  # Continue with other formats if doesn't match
                raise ValueError
            return handle_timezone(parsed)
        return super().strptime(value, format)


class BaseCSVField(forms.Field):
    """
    Base field for validating CSV types. Value validation is performed by
    secondary base classes.
    ex::
        class IntegerCSVField(BaseCSVField, filters.IntegerField):
            pass
    """
    base_widget_class = BaseCSVWidget

    def __init__(self, *args, **kwargs):
        widget = kwargs.get('widget') or self.widget
        kwargs['widget'] = self._get_widget_class(widget)

        super().__init__(*args, **kwargs)

    def _get_widget_class(self, widget):
        # passthrough, allows for override
        if isinstance(widget, BaseCSVWidget) or (
                isinstance(widget, type) and
                issubclass(widget, BaseCSVWidget)):
            return widget

        # complain since we are unable to reconstruct widget instances
        assert isinstance(widget, type), \
            "'%s.widget' must be a widget class, not %s." \
            % (self.__class__.__name__, repr(widget))

        bases = (self.base_widget_class, widget, )
        return type(str('CSV%s' % widget.__name__), bases, {})

    def clean(self, value):
        if value is None:
            return None
        return [super(BaseCSVField, self).clean(v) for v in value]


class BaseRangeField(BaseCSVField):
    # Force use of text input, as range must always have two inputs. A date
    # input would only allow a user to input one value and would always fail.
    widget = CSVWidget

    default_error_messages = {
        'invalid_values': _('Range query expects two values.')
    }

    def clean(self, value):
        value = super().clean(value)

        if value is not None and len(value) != 2:
            raise forms.ValidationError(
                self.error_messages['invalid_values'],
                code='invalid_values')

        return value


class ChoiceIterator(object):
    # Emulates the behavior of ModelChoiceIterator, but instead wraps
    # the field's _choices iterable.

    def __init__(self, field, choices):
        self.field = field
        self.choices = choices

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        if self.field.null_label is not None:
            yield (self.field.null_value, self.field.null_label)

        # Python 2 lacks 'yield from'
        for choice in self.choices:
            yield choice

    def __len__(self):
        add = 1 if self.field.empty_label is not None else 0
        add += 1 if self.field.null_label is not None else 0
        return len(self.choices) + add


class ModelChoiceIterator(forms.models.ModelChoiceIterator):
    # Extends the base ModelChoiceIterator to add in 'null' choice handling.
    # This is a bit verbose since we have to insert the null choice after the
    # empty choice, but before the remainder of the choices.

    def __iter__(self):
        iterable = super().__iter__()

        if self.field.empty_label is not None:
            yield next(iterable)
        if self.field.null_label is not None:
            yield (self.field.null_value, self.field.null_label)

        # Python 2 lacks 'yield from'
        for value in iterable:
            yield value

    def __len__(self):
        add = 1 if self.field.null_label is not None else 0
        return super().__len__() + add


class ChoiceIteratorMixin(object):
    def __init__(self, *args, **kwargs):
        self.null_label = kwargs.pop('null_label', settings.NULL_CHOICE_LABEL)
        self.null_value = kwargs.pop('null_value', settings.NULL_CHOICE_VALUE)

        super().__init__(*args, **kwargs)

    def _get_choices(self):
        return super()._get_choices()

    def _set_choices(self, value):
        super()._set_choices(value)
        value = self.iterator(self, self._choices)

        self._choices = self.widget.choices = value
    choices = property(_get_choices, _set_choices)


# Unlike their Model* counterparts, forms.ChoiceField and forms.MultipleChoiceField do not set empty_label
class ChoiceField(ChoiceIteratorMixin, forms.ChoiceField):
    iterator = ChoiceIterator

    def __init__(self, *args, **kwargs):
        self.empty_label = kwargs.pop('empty_label', settings.EMPTY_CHOICE_LABEL)
        super().__init__(*args, **kwargs)


class MultipleChoiceField(ChoiceIteratorMixin, forms.MultipleChoiceField):
    iterator = ChoiceIterator

    def __init__(self, *args, **kwargs):
        self.empty_label = None
        super().__init__(*args, **kwargs)


class ModelChoiceField(ChoiceIteratorMixin, forms.ModelChoiceField):
    iterator = ModelChoiceIterator

    def to_python(self, value):
        # bypass the queryset value check
        if self.null_label is not None and value == self.null_value:
            return value
        return super().to_python(value)


class ModelMultipleChoiceField(ChoiceIteratorMixin, forms.ModelMultipleChoiceField):
    iterator = ModelChoiceIterator

    def _check_values(self, value):
        null = self.null_label is not None and value and self.null_value in value
        if null:  # remove the null value and any potential duplicates
            value = [v for v in value if v != self.null_value]

        result = list(super()._check_values(value))
        result += [self.null_value] if null else []
return result


_________________________________________________________________________________


https://gist.githubusercontent.com/edgartaor/53de162f06ac49e770f8/raw/22aefc9899e00e7f06d063359b39718bdb3939c9/filters.py




class ItemFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(name='price', lookup_type='gte')
    max_price = django_filters.NumberFilter(name='price', lookup_type='lte')
    category = django_filters.CharFilter(name='category__slug', lookup_type='iexact')
    title = django_filters.MethodFilter(name='title', action='icontains_any_word_title')
    description = django_filters.MethodFilter(name='description', action='icontains_any_word_description')

    class Meta:
        model = Item
        fields = ['category', 'min_price', 'max_price', 'negotiable', 'title', 'description']

    def icontains_any_word_title(self, queryset, value):
        query_words = str(value).split(" ") #Get the word in a list
        for w in query_words:
            if len(w) < 3: #Min length
                query_words.remove(w)

        if not query_words:
            return queryset
        return queryset.filter(reduce(lambda x, y: x | y, [Q(title__icontains=word) for word in query_words]))


    def icontains_any_word_description(self, queryset, value):
        query_words = str(value).split(" ")
        for w in query_words:
            if len(w) < 3:
                query_words.remove(w)
        if not query_words:
            return queryset
        return queryset.filter(reduce(lambda x, y: x | y, [Q(description__icontains=word) for word in query_words]))