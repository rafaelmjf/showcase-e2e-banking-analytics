select *
from (
    values
        ('4010'::text, 'Monthly individual balance sheet'::text, true::boolean, 'monthly'::text),
        ('4016'::text, 'Semiannual individual balance sheet'::text, false::boolean, 'semiannual'::text)
) as documents(document_code, document_name, analytical_allowed, source_frequency)
