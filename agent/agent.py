import subprocess
import re
import json
import argparse
import requests

def send_results(results, coordinator_url):
    """
    Sends the parsed results to the coordinator.
    """
    try:
        response = requests.post(coordinator_url, json=results)
        response.raise_for_status()
        print(f"Successfully sent results to {coordinator_url}")
        print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error sending results to coordinator: {e}")

def run_dig(domain, record_type='A', target_server=None):
    """
    Executes a dig command for a given domain and parses the output.

    Args:
        domain (str): The domain to query.
        record_type (str): The DNS record type to query (e.g., A, AAAA, MX).
        target_server (str): The specific DNS server to query.

    Returns:
        dict: A dictionary containing the parsed dig results.
    """
    command = ['dig']
    if target_server:
        command.append(f'@{target_server}')
    command.extend([domain, record_type])

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output = result.stdout

        # Parse output
        query_time_match = re.search(r';; Query time: (\d+) msec', output)
        status_match = re.search(r'status: (\w+),', output)

        answer_section_match = re.search(r';; ANSWER SECTION:\n(.*?)\n\n', output, re.DOTALL)

        records = []
        if answer_section_match:
            answer_section = answer_section_match.group(1)
            for line in answer_section.splitlines():
                if line.strip() and not line.startswith(';'):
                    parts = re.split(r'\s+', line)
                    if len(parts) >= 5:
                        records.append({
                            'name': parts[0],
                            'ttl': int(parts[1]),
                            'class': parts[2],
                            'type': parts[3],
                            'data': parts[4]
                        })

        return {
            'domain': domain,
            'record_type': record_type,
            'query_time_ms': int(query_time_match.group(1)) if query_time_match else None,
            'status': status_match.group(1) if status_match else 'UNKNOWN',
            'records': records
        }

    except subprocess.CalledProcessError as e:
        return {
            'error': str(e),
            'stdout': e.stdout,
            'stderr': e.stderr
        }
    except FileNotFoundError:
        return {
            'error': 'dig command not found. Please ensure it is installed and in your PATH.'
        }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DNS Dig-based Monitoring Agent')
    parser.add_argument('domain', help='The domain to query')
    parser.add_argument('-t', '--type', default='A', help='Record type (A, AAAA, MX, etc.)')
    parser.add_argument('-s', '--server', help='DNS server to use')
    parser.add_argument('-c', '--coordinator', help='Coordinator URL to send results to')
    args = parser.parse_args()

    results = run_dig(args.domain, args.type, args.server)

    if args.coordinator:
        send_results(results, args.coordinator)
    else:
        print(json.dumps(results, indent=2))