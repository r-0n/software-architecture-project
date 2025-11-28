from django import forms


class OrderHistoryFilterForm(forms.Form):
    """Form for filtering and searching order history"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by order ID or product name...'
        })
    )
    status = forms.ChoiceField(
        choices=[
            ('', 'All Statuses'),
            ('completed', 'Completed'),
            ('pending', 'Pending'),
            ('returned', 'Returned'),
            ('refunded', 'Refunded'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    only_no_returns = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Only show orders with no return requests",
    )

