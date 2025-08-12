import subprocess
import os

class WifiManager:
    """
    Handles interactions with NetworkManager using nmcli.
    """

    @staticmethod
    def get_saved_connections():
        """
        Retrieves a list of saved Wi-Fi connections and their passwords.

        Returns:
            list: A list of dictionaries, each containing 'name', 'ssid', 'password'.
                  Returns an empty list on failure.
        """
        try:
            # Get list of connection names and types
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show'],
                capture_output=True,
                text=True,
                check=True
            )
            
            connections = []
            for line in result.stdout.strip().split('\n'):
                if line: # Skip empty lines
                    parts = line.split(':')
                    if len(parts) >= 2 and parts[1] == '802-11-wireless': # Check if type is Wi-Fi
                        conn_name = parts[0]
                        # Get SSID and password for the Wi-Fi connection
                        ssid_result = subprocess.run(
                            ['nmcli', '-s', '-t', '-f', '802-11-wireless.ssid', 'connection', 'show', conn_name],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        # The output format is '802-11-wireless.ssid:<SSID>'
                        ssid_line = ssid_result.stdout.strip()
                        if ssid_line.startswith('802-11-wireless.ssid:'):
                            ssid = ssid_line.split(':', 1)[1]
                        else:
                            # If ssid field is empty, use the connection name
                            ssid = conn_name
                        
                        # Get password
                        passwd_result = subprocess.run(
                            ['nmcli', '-s', '-t', '-f', '802-11-wireless-security.psk', 'connection', 'show', conn_name],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        # The output format is '802-11-wireless-security.psk:<PASSWORD>'
                        passwd_line = passwd_result.stdout.strip()
                        if passwd_line.startswith('802-11-wireless-security.psk:'):
                            password = passwd_line.split(':', 1)[1]
                        else:
                            password = '' # No password or not WPA/WPA2

                        connections.append({
                            'name': conn_name,
                            'ssid': ssid,
                            'password': password
                        })
            
            return connections
        except subprocess.CalledProcessError as e:
            print(f'Error retrieving connections: {e}')
            return []
        except Exception as e:
            print(f'Unexpected error in get_saved_connections: {e}')
            return []

    @staticmethod
    def connect_to_network(ssid, password=''):
        """
        Attempts to connect to a network using nmcli.

        Args:
            ssid (str): The SSID of the network.
            password (str, optional): The password for the network.

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # This is a simplified approach. A more robust one would involve creating a temporary profile.
            # For now, we assume a profile already exists or we try to connect directly (which might not work).
            # A better way is to create a temporary connection profile.
            # Let's try connecting using the ssid directly if a profile exists.
            # If not, this won't work. For a full implementation, creating a temporary profile is needed.
            
            # Check if a connection with this SSID already exists
            existing_conns = WifiManager.get_saved_connections()
            conn_name = None
            for conn in existing_conns:
                if conn['ssid'] == ssid:
                    conn_name = conn['name']
                    break
            
            if conn_name:
                result = subprocess.run(
                    ['nmcli', 'connection', 'up', conn_name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return True, f'Successfully connected to \'{ssid}\' using existing profile \'{conn_name}\'.'
                else:
                    return False, f'Failed to connect using existing profile \'{conn_name}\': {result.stderr}'
            else:
                # Attempt to create a temporary connection profile (this requires more details)
                # This is a placeholder for a more complex implementation
                # We'll just return a message indicating it's not fully implemented here
                # and suggest using the 'Save Profile' feature first.
                return False, f'No existing profile found for \'{ssid}\'. Please save the profile first.'
                
        except Exception as e:
            return False, f'Unexpected error in connect_to_network: {e}'

    @staticmethod
    def save_profile(ssid, password='', security='WPA'): # Default to WPA as it's common
        """
        Saves a new Wi-Fi connection profile using nmcli.

        Args:
            ssid (str): The SSID of the network.
            password (str, optional): The password for the network.
            security (str, optional): The security type (e.g., 'WPA', 'WEP', ''). Defaults to 'WPA'.

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Create a new connection profile
            # Use a unique name, e.g., 'Temp_WiFi_<SSID>' or just SSID if unique enough
            profile_name = f'WiFi_{ssid}'
            
            cmd = ['nmcli', 'connection', 'add', 'type', 'wifi', 'con-name', profile_name, 'ssid', ssid]
            
            # Add security settings if password is provided
            if password:
                if security.upper() == 'WPA':
                    cmd.extend(['wifi-sec.key-mgmt', 'wpa-psk', 'wifi-sec.psk', password])
                elif security.upper() == 'WEP':
                    # Note: WEP is deprecated and less secure
                    cmd.extend(['wifi-sec.key-mgmt', 'none', 'wifi-sec.wep-key0', password])
                # Add other security types as needed
            
            # Execute the command to create the profile
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, f'Profile \'{profile_name}\' for \'{ssid}\' saved successfully.'
            else:
                return False, f'Failed to save profile: {result.stderr}'
                
        except Exception as e:
            return False, f'Unexpected error in save_profile: {e}'
