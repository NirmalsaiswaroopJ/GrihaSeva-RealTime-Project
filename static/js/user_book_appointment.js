// This is only for reference purpose as inline formating is already done.
document.getElementById('service').addEventListener('change', function() {
            var service = this.value;
            var providerDropdown = document.getElementById('service-provider');
            providerDropdown.innerHTML = '<option value="">Select a service provider</option>';

            if (service) {
                fetch(`/get-providers/${service}`)
                    .then(response => response.json())
                    .then(data => {
                        data.forEach(function(provider) {
                            var option = document.createElement('option');
                            option.value = provider;
                            option.text = provider;
                            providerDropdown.add(option);
                        });
                    })
                    .catch(error => console.error('Error:', error));
            }
        });
