import speedtest
st = speedtest.Speedtest(secure=True)

st.get_servers()
st.get_best_server()

st.download()

print(st.results)