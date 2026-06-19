try:
    from escpos.printer import Usb
    _printer_available = True
except Exception:
    _printer_available = False


def print_receipt(sale_data):
    if not _printer_available:
        print("[Printer] Library not available — skipped")
        return False

    try:
        p = Usb(0x04b8, 0x0202, timeout=5, in_ep=0x82, out_ep=0x02)
        p.set(align='center')
        p.text("CHEERS CLUB\n")
        p.text("===============\n\n")
        p.set(align='left')

        for item in sale_data['items']:
            line = f"{item['name']}  x{item['qty']}  KES {item['total']:.0f}\n"
            p.text(line)

        p.text("\n---------------\n")
        p.set(align='right')
        p.text(f"TOTAL:    KES {sale_data['total']:.0f}\n")
        p.text(f"{sale_data['payment_method']}\n")
        p.text(f"Attendant: {sale_data['staff']}\n")
        from datetime import datetime
        p.text(datetime.now().strftime('%d/%m/%Y %H:%M\n'))
        p.set(align='center')
        p.text("===============\n")
        p.text("Thank you, come again!\n")
        p.cut()
        return True
    except Exception as e:
        print(f"[Printer] Error: {e}")
        return False


def print_test():
    if not _printer_available:
        return "Printer library not available"

    try:
        p = Usb(0x04b8, 0x0202, timeout=5, in_ep=0x82, out_ep=0x02)
        p.set(align='center')
        p.text("CHEERS CLUB\n")
        p.text("Printer Test OK\n")
        p.cut()
        return "Printed successfully"
    except Exception as e:
        return f"Printer error: {e}"
