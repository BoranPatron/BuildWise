#!/usr/bin/env python3
"""
Quick check script to see if BuildWise fee was created for Quote 1
"""
import sqlite3

conn = sqlite3.connect('buildwise.db')
cursor = conn.cursor()

print("=" * 80)
print("QUOTE 1 DETAILS")
print("=" * 80)
cursor.execute('SELECT id, project_id, milestone_id, status, total_amount, currency FROM quotes WHERE id = 1')
quote = cursor.fetchone()
if quote:
    print(f"Quote ID: {quote[0]}")
    print(f"Project ID: {quote[1]}")
    print(f"Milestone ID: {quote[2]}")
    print(f"Status: {quote[3]}")
    print(f"Total Amount: {quote[4]} {quote[5]}")
else:
    print("Quote 1 NOT FOUND")

print("\n" + "=" * 80)
print("BUILDWISE FEES FOR QUOTE 1")
print("=" * 80)
cursor.execute('SELECT * FROM buildwise_fees WHERE quote_id = 1')
fees = cursor.fetchall()
if fees:
    for fee in fees:
        print(f"Fee: {fee}")
else:
    print("NO BuildWise fees found for Quote 1")

print("\n" + "=" * 80)
print("COST POSITIONS FOR QUOTE 1")
print("=" * 80)
cursor.execute('SELECT id, quote_id, title, amount FROM cost_positions WHERE quote_id = 1')
positions = cursor.fetchall()
if positions:
    for pos in positions:
        print(f"Cost Position ID: {pos[0]}, Quote ID: {pos[1]}, Title: {pos[2]}, Amount: {pos[3]}")
else:
    print("NO cost positions found for Quote 1")

print("\n" + "=" * 80)
print("ALL BUILDWISE FEES IN DATABASE")
print("=" * 80)
cursor.execute('SELECT id, quote_id, invoice_number, fee_amount, status FROM buildwise_fees')
all_fees = cursor.fetchall()
if all_fees:
    for fee in all_fees:
        print(f"Fee ID: {fee[0]}, Quote ID: {fee[1]}, Invoice: {fee[2]}, Amount: {fee[3]}, Status: {fee[4]}")
else:
    print("NO BuildWise fees found in database at all")

conn.close()



