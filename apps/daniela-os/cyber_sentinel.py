import concurrent.futures
import socket


def scan_port(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    result = sock.connect_ex((ip, port))
    sock.close()
    return port if result == 0 else None


def audit_network(target_ip):
    """Escanea puertos críticos de un dispositivo específico."""
    common_ports = [21, 22, 23, 80, 443, 8080, 8443, 3000]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_port = {
            executor.submit(scan_port, target_ip, port): port for port in common_ports
        }
        for future in concurrent.futures.as_completed(future_to_port):
            port = future.result()
            if port:
                results.append(port)
    return results
