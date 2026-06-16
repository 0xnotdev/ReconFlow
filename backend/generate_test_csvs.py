import csv
from datetime import datetime, timedelta

now = datetime.utcnow()

# ----------------- STRIPE CSV -----------------
stripe_headers = ['id', 'Amount', 'Fee', 'Net', 'Created (UTC)', 'Currency', 'Status', 'Customer Email']
stripe_data = [
    # Normal transaction (reconciled)
    ['ch_normal_1', '150.00', '4.65', '145.35', (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), 'usd', 'succeeded', 'alice@example.com'],
    # Missing in QB
    ['ch_missing_1', '2400.00', '69.90', '2330.10', (now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'), 'usd', 'succeeded', 'sarah@example.com'],
    # Duplicate in QB
    ['ch_dup_1', '1850.00', '53.95', '1796.05', (now - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'), 'usd', 'succeeded', 'james@example.com'],
    # Refund mismatch
    ['ch_ref_1', '3200.00', '93.10', '3106.90', (now - timedelta(days=4)).strftime('%Y-%m-%d %H:%M:%S'), 'usd', 'refunded', 'elena@example.com'],
    # Fee variance (expected fee for 5000 is 5000*0.029 + 0.30 = 145.30. We put 180.00)
    ['ch_fee_1', '5000.00', '180.00', '4820.00', (now - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'), 'usd', 'succeeded', 'highfee@example.com']
]

with open('test_stripe.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(stripe_headers)
    writer.writerows(stripe_data)

# ----------------- QUICKBOOKS CSV -----------------
qb_headers = ['Num', 'Date', 'Transaction Type', 'Amount', 'Name', 'Memo/Description']
qb_data = [
    # Normal transaction
    ['1001', (now - timedelta(days=1)).strftime('%m/%d/%Y'), 'Payment', '150.00', 'Alice', 'Paid'],
    # Missing from Stripe (we don't flag this currently, but good for noise)
    ['1002', (now - timedelta(days=2)).strftime('%m/%d/%Y'), 'Payment', '50.00', 'Noise', 'Paid'],
    # Duplicates for James (ch_dup_1)
    ['1003a', (now - timedelta(days=3)).strftime('%m/%d/%Y'), 'Payment', '1850.00', 'James', 'Paid'],
    ['1003b', (now - timedelta(days=3)).strftime('%m/%d/%Y'), 'Payment', '1850.00', 'James', 'Duplicate Entry Error'],
    # Refund mismatch (Refund missing in QB, so we only put the original payment)
    ['1004', (now - timedelta(days=4)).strftime('%m/%d/%Y'), 'Payment', '3200.00', 'Elena', 'Paid but refund not recorded'],
    # Fee variance transaction
    ['1005', (now - timedelta(days=5)).strftime('%m/%d/%Y'), 'Payment', '5000.00', 'HighFee Inc', 'Paid']
]

with open('test_quickbooks.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(qb_headers)
    writer.writerows(qb_data)

# ----------------- SHOPIFY CSV -----------------
shopify_headers = ['Name', 'Total', 'Created at', 'Financial Status', 'Email', 'Payment Method']
shopify_data = [
    # Normal transaction
    ['SH-100', '150.00', (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S +0000'), 'paid', 'alice@example.com', 'stripe'],
    # Revenue leak (paid in Shopify, but no Stripe charge exists)
    ['SH-LEAK', '1200.00', (now - timedelta(days=6)).strftime('%Y-%m-%d %H:%M:%S +0000'), 'paid', 'leak@example.com', 'stripe']
]

with open('test_shopify.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(shopify_headers)
    writer.writerows(shopify_data)

print("Test CSV files generated successfully!")
