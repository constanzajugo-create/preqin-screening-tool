html_table = f"""
<div style="overflow-x: auto; width: 100%;">
<table style="width: 100%; table-layout: fixed;">
    <thead>
        <tr>
            <th>GP (Fund Manager)</th>
            <th>Asset Class</th>
            <th>Strategy</th>
            <th>Region</th>
            <th># Funds</th>
            <th>Last Vintage</th>
            <th>Last Fund Size (USDm)</th>
            <th>Total AUM Considerado (USDm)</th>
            <th>GP Total AUM (USDm)</th>
            <th>Score</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>{selected_gp}</td>
            <td>{asset_class}</td>
            <td>{strategy}</td>
            <td>{region}</td>
            <td>{num_funds}</td>
            <td>{last_vintage}</td>
            <td>{last_fund_size:,.0f}</td>
            <td>{total_aum_considered:,.0f}</td>
            <td>{gp_total_aum:,.0f}</td>
            <td><b>{gp_score}</b></td>
        </tr>
    </tbody>
</table>
</div>
"""




