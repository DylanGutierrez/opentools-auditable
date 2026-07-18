"""Routes scan."""
import re
from flask import Blueprint, request, jsonify
from config import NUCLEI_RATE_LIMITS
from database import get_db_connection, get_convention_by_audit
from services.settings_service import (
    get_param_rows,
    normalize_bool,
    normalize_severity,
    normalize_tuning,
    normalize_wpscan_enumeration,
)
from services.scan_helpers import (
    run_scan_command,
    command_log_text,
    insert_tool_log,
    parse_nmap_open_ports,
    add_nmap_export,
    add_nikto_export,
    add_wpscan_export,
    add_nuclei_export,
    tool_target_urls,
)
from services.security_feeds import fetch_cve_details, update_epss_for_cve

scan_bp = Blueprint("scan", __name__)

# Lancement des outils de scan sélectionnés.
@scan_bp.route('/api/scan/launch', methods=['POST'])
def launch_scan():
    conn = None
    cursor = None

    try:
        data = request.json or {}
        audit_id = data.get("audit_id")
        selected_tools = data.get("tools") or ["nmap"]
        selected_tools = {str(tool).lower() for tool in selected_tools}

        if not audit_id:
            return jsonify({"error": "audit_id manquant."}), 400

        if not selected_tools:
            return jsonify({"error": "Aucun outil sélectionné."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        conv = get_convention_by_audit(cursor, audit_id)

        if not conv or not conv['signed']:
            return jsonify({"error": "La convention d'audit doit être signée pour lancer une analyse."}), 403

        settings = get_param_rows(cursor)

        cursor.execute("""
            SELECT
                li.id AS list_ip_id,
                li.ip,
                li.true_cmd_port,
                lp.id AS list_port_id,
                lp.port_number
            FROM list_ip li
            LEFT JOIN list_port lp ON lp.list_ip_id = li.id
            WHERE li.convention_id = %s
            ORDER BY li.id, lp.port_number
        """, (conv["id"],))
        rows = cursor.fetchall()

        grouped = {}
        for row in rows:
            list_ip_id = row["list_ip_id"]
            if list_ip_id not in grouped:
                grouped[list_ip_id] = {
                    "list_ip_id": list_ip_id,
                    "ip": row["ip"],
                    "true_cmd_port": row.get("true_cmd_port") or "",
                    "ports": []
                }
            if row["port_number"] is not None:
                grouped[list_ip_id]["ports"].append(row["port_number"])

        results = {}

        for target in grouped.values():
            ip = target["ip"]
            list_ip_id = target["list_ip_id"]
            ports = sorted(set(target["ports"]))
            target_result = []

            if str(target.get("true_cmd_port") or "").strip().lower() == "auto":
                auto_cmd = ["nmap", "-sS", "-sU", "-p-", ip]
                auto_proc = run_scan_command(auto_cmd)
                auto_ports = parse_nmap_open_ports(auto_proc.stdout)
                ports = auto_ports
                log_text = command_log_text(
                    auto_cmd,
                    auto_proc,
                    context=f"Découverte automatique des ports. Ports retenus : {','.join(map(str, ports)) or 'aucun'}"
                )
                insert_tool_log(cursor, "log_nmap", list_ip_id, log_text)
                target_result.append({
                    "tool": "nmap_auto",
                    "cmd": auto_cmd,
                    "returncode": auto_proc.returncode,
                    "ports": ports,
                })
                conn.commit()

            if "nmap" in selected_tools:
                nmap_setting = settings["nmap"]
                nmap_cmd = ["nmap", "-sV", "--script", "vulners", ip]
                if ports:
                    nmap_cmd.extend(["-p", ",".join(str(p) for p in ports)])
                report_files = add_nmap_export(nmap_cmd, nmap_setting, ip, suffix="vulners")
                nmap_proc = run_scan_command(nmap_cmd)
                insert_tool_log(cursor, "log_nmap", list_ip_id, command_log_text(nmap_cmd, nmap_proc, report_files=report_files))

                cves = re.findall(r"(CVE-\d{4}-\d{4,7})", nmap_proc.stdout or "")
                print(f"[*] CVE trouvées pour {ip} : {cves}")

                for cve in sorted(set(cves)):
                    cursor.execute("""
                        SELECT
                            id,
                            CVSS,
                            description,
                            criticity,
                            CWE,
                            remediation,
                            risk,
                            source,
                            external_link
                        FROM vulnerabilities
                        WHERE CVE = %s AND used_tool = %s
                        LIMIT 1
                    """, (cve, "Nmap"))

                    existing_vuln = cursor.fetchone()

                    needs_nvd = (
                        not existing_vuln
                        or not existing_vuln.get("description")
                        or not existing_vuln.get("CVSS")
                        or not existing_vuln.get("CWE")
                    )

                    if needs_nvd:
                        details = fetch_cve_details(cve, cursor=cursor, list_ip_id=list_ip_id)
                    else:
                        details = {}

                    cvss = details.get("cvss")
                    vulnerability_name = details.get("vulnerability_name") or cve
                    criticity = details.get("criticity")
                    description = details.get("description")
                    risk = details.get("risk")
                    cwe = details.get("cwe")
                    remediation = details.get("remediation")
                    source = details.get("source") or ("NVD" if details else None)
                    external_link = details.get("external_link")

                    if existing_vuln:
                        vuln_id = existing_vuln["id"] if isinstance(existing_vuln, dict) else existing_vuln[0]

                        if details:
                            cursor.execute("""
                                UPDATE vulnerabilities
                                SET
                                    CVSS = COALESCE(NULLIF(%s, ''), CVSS),
                                    vulnerability_name = COALESCE(NULLIF(%s, ''), vulnerability_name),
                                    criticity = COALESCE(%s, criticity),
                                    description = COALESCE(NULLIF(%s, ''), description),
                                    risk = COALESCE(NULLIF(%s, ''), risk),
                                    CWE = COALESCE(NULLIF(%s, ''), CWE),
                                    remediation = COALESCE(NULLIF(%s, ''), remediation),
                                    source = COALESCE(NULLIF(%s, ''), source),
                                    external_link = COALESCE(NULLIF(%s, ''), external_link),
                                    ip_id = COALESCE(ip_id, %s)
                                WHERE id = %s
                            """, (
                                cvss,
                                vulnerability_name,
                                criticity,
                                description,
                                risk,
                                cwe,
                                remediation,
                                source,
                                external_link,
                                list_ip_id,
                                vuln_id
                            ))

                    else:
                        cursor.execute("""
                            INSERT INTO vulnerabilities (
                                CVE,
                                CVSS,
                                vulnerability_name,
                                criticity,
                                description,
                                risk,
                                CWE,
                                remediation,
                                source,
                                external_link,
                                used_tool,
                                ip_id
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            cve,
                            cvss,
                            vulnerability_name,
                            criticity,
                            description,
                            risk,
                            cwe,
                            remediation,
                            source,
                            external_link,
                            "Nmap",
                            list_ip_id
                        ))

                    updated = update_epss_for_cve(cursor, cve, list_ip_id=list_ip_id)
                    print(f"[*] EPSS mis à jour pour {cve} : {updated}")
                    conn.commit()

                target_result.append({
                    "tool": "nmap",
                    "cmd": nmap_cmd,
                    "returncode": nmap_proc.returncode,
                })
                conn.commit()

                if int(nmap_setting.get("aggressiveness") or 0) >= 7:
                    aggressive_cmd = ["nmap", "-A", ip]
                    if ports:
                        aggressive_cmd.extend(["-p", ",".join(str(p) for p in ports)])
                    else:
                        aggressive_cmd.extend(["-p-" ])
                    aggressive_reports = add_nmap_export(aggressive_cmd, nmap_setting, ip, suffix="aggressive")
                    aggressive_proc = run_scan_command(aggressive_cmd)
                    insert_tool_log(
                        cursor,
                        "log_nmap",
                        list_ip_id,
                        command_log_text(aggressive_cmd, aggressive_proc, report_files=aggressive_reports, context="Scan agressif déclenché car agressivité Nmap >= 7")
                    )
                    target_result.append({
                        "tool": "nmap_aggressive",
                        "cmd": aggressive_cmd,
                        "returncode": aggressive_proc.returncode,
                    })
                    conn.commit()

            if "nikto" in selected_tools:
                nikto_setting = settings["nikto"]
                nikto_cmd = ["nikto", "-h", ip, "-ssl"]
                tuning = normalize_tuning(nikto_setting.get("tuning_option"))
                if tuning:
                    nikto_cmd.extend(["-Tuning", tuning])
                report_files = add_nikto_export(nikto_cmd, nikto_setting, ip)
                nikto_proc = run_scan_command(nikto_cmd)
                insert_tool_log(cursor, "log_nikto", list_ip_id, command_log_text(nikto_cmd, nikto_proc, report_files=report_files))
                target_result.append({
                    "tool": "nikto",
                    "cmd": nikto_cmd,
                    "returncode": nikto_proc.returncode,
                })
                conn.commit()

            if "wpscan" in selected_tools:
                wpscan_setting = settings["wpscan"]
                enum_mode, enum_option = normalize_wpscan_enumeration(wpscan_setting.get("enumeration_mode"))
                enumerate_value = enum_option.replace("-e ", "")
                for url in tool_target_urls(ip, ports):
                    wpscan_cmd = ["wpscan", "--url", url, "--enumerate", enumerate_value]
                    if normalize_bool(wpscan_setting.get("aggressiveness")):
                        wpscan_cmd.extend(["--plugins-detection", "aggressive"])
                    report_files = add_wpscan_export(wpscan_cmd, wpscan_setting, ip)
                    wpscan_proc = run_scan_command(wpscan_cmd)
                    insert_tool_log(
                        cursor,
                        "log_wpscan",
                        list_ip_id,
                        command_log_text(wpscan_cmd, wpscan_proc, report_files=report_files, context=f"Mode d'énumération : {enum_mode}"),
                        enumeration_option=enum_option
                    )
                    target_result.append({
                        "tool": "wpscan",
                        "cmd": wpscan_cmd,
                        "returncode": wpscan_proc.returncode,
                    })
                    conn.commit()

            if "nuclei" in selected_tools:
                nuclei_setting = settings["nuclei"]
                severity = normalize_severity(nuclei_setting.get("severity"))
                rate_limit = NUCLEI_RATE_LIMITS.get(int(nuclei_setting.get("aggressiveness") or 0), 10)
                nuclei_ports = ports or [443]

                for port in nuclei_ports:
                    nuclei_cmd = [
                        "nuclei",
                        "-u", f"{ip}:{port}",
                        "-tags", "exposure,misconfig,cve,wordpress,panel,tech",
                        "-severity", severity,
                        "-rate-limit", str(rate_limit),
                    ]
                    report_files = add_nuclei_export(nuclei_cmd, nuclei_setting, ip, suffix=str(port))
                    nuclei_proc = run_scan_command(nuclei_cmd)
                    insert_tool_log(
                        cursor,
                        "log_nuclei",
                        list_ip_id,
                        command_log_text(nuclei_cmd, nuclei_proc, report_files=report_files, context=f"Criticités : {severity}; rate-limit : {rate_limit}")
                    )
                    target_result.append({
                        "tool": "nuclei",
                        "cmd": nuclei_cmd,
                        "returncode": nuclei_proc.returncode,
                        "port": port,
                    })
                    conn.commit()

            results[ip] = target_result

        return jsonify({"message": "Analyse lancée avec succès.", "raw": results})

    except Exception as e:
        print(f"[!] Erreur /api/scan/launch : {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
