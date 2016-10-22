from rest_framework import serializers


class QuantizedDecimalField(serializers.DecimalField):
    def validate_precision(self, value):
        """
        Overrides default precision validation to allow the field silently quantize according to field spec, while still
        validating the max whole digits.
        """
        sign, digittuple, exponent = value.as_tuple()

        if exponent >= 0:
            # 1234500.0
            total_digits = len(digittuple) + exponent
            whole_digits = total_digits
        elif len(digittuple) > abs(exponent):
            # 123.45
            total_digits = len(digittuple)
            whole_digits = total_digits - abs(exponent)
        else:
            whole_digits = 0

        if self.max_whole_digits is not None and whole_digits > self.max_whole_digits:
            self.fail('max_whole_digits', max_whole_digits=self.max_whole_digits)

        return value
