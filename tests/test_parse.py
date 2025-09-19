from __future__ import annotations

from textwrap import dedent

from smartmoney.parse.form4 import parse_form4_transactions
from smartmoney.parse.form13 import parse_13d_g, parse_13f_holdings


def test_form4_parser_extracts_open_market_buys():
    sample = {
        "issuerTradingSymbol": "ABCD",
        "reportingOwners": [
            {
                "reportingOwner": {"rptOwnerName": "Jane Doe"},
                "reportingOwnerRelationship": {"officerTitle": "Chief Financial Officer"},
            }
        ],
        "nonDerivativeTable": {
            "nonDerivativeTransaction": {
                "transactionCoding": {"transactionCode": "P"},
                "transactionAmounts": {
                    "transactionShares": {"value": "1200"},
                    "transactionPricePerShare": {"value": "5.25"},
                },
                "transactionDate": {"value": "2024-03-05"},
            }
        },
    }

    df = parse_form4_transactions(sample)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["ticker"] == "ABCD"
    assert row["insider_role"] == "CFO"
    assert row["transaction_value"] == 1200 * 5.25


def test_parse_13d_g_extracts_percent_and_date():
    text = dedent(
        """
        UNITED STATES
        SCHEDULE 13D
        Name of Reporting Person: Alpha Capital
        Filed on March 12, 2024
        Percentage of Class Represented by Amount in Row 11: 9.8%
        """
    )

    rows = parse_13d_g(text, ticker="ABCD")
    assert rows[0]["filer"] == "Alpha Capital"
    assert rows[0]["percent"] == 9.8
    assert rows[0]["form_type"] == "13D"
    assert rows[0]["filing_date"] == "2024-03-12"


def test_parse_13f_holdings_normalises_values():
    xml = dedent(
        """
        <form13FInformationTable>
          <headerData>
            <filingDate>2024-05-15</filingDate>
            <filerInfo>
              <filer>
                <credentials><cik>0000123456</cik></credentials>
                <name>Blue Whale</name>
              </filer>
            </filerInfo>
          </headerData>
          <infoTable>
            <nameOfIssuer>ABCD</nameOfIssuer>
            <cusip>123456789</cusip>
            <value>2500</value>
            <shrsOrPrnAmt><sshPrnamt>100000</sshPrnamt></shrsOrPrnAmt>
          </infoTable>
        </form13FInformationTable>
        """
    )
    rows = parse_13f_holdings(xml, {"123456789": "ABCD"})
    assert rows[0]["value"] == 2500 * 1000
    assert rows[0]["shares"] == 100000
    assert rows[0]["filing_date"] == "2024-05-15"
