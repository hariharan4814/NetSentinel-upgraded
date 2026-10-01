export const issues = [
  { id: "slow", title: "My internet feels slow", short: "Slow browsing", icon: "globe", description: "Pages take forever. Downloads keep waiting.", steps: [
    ["Compare two different websites", "If only one is slow, that website may be busy. Check its official status page before changing your network."],
    ["Pause one busy download or backup", "Pause a download or cloud backup you control, then run another check. Change one thing at a time so you can compare."],
    ["Try closer to your router", "If you use Wi-Fi, try the same device nearer the router. If available, compare a wired connection."],
    ["Compare another device", "Try a second device on the same network. If several devices struggle with several websites, contact your provider with the times and symptoms."],
  ] },
  { id: "calls", title: "Video calls keep freezing", short: "Laggy video calls", icon: "pulse", description: "Choppy audio, frozen faces, awkward pauses.", steps: [
    ["Check the meeting app’s status", "Try its official status page. A problem with one meeting service does not necessarily mean your home connection is failing."],
    ["Reduce competing activity", "Pause your own uploads and backups. Temporarily lower video quality or turn off your camera and see whether audio improves."],
    ["Compare Wi-Fi and a wired connection", "Move closer to the router, or use Ethernet if available. Keep the same call app so the comparison is useful."],
    ["Keep a short record", "Note when the call broke up and whether other websites worked. This check measures this website, not your meeting server or real-time media quality."],
  ] },
  { id: "drops", title: "My connection keeps dropping", short: "Random disconnections", icon: "wifi", description: "Online one moment. Offline the next.", steps: [
    ["Notice what actually disconnects", "Check whether your device leaves Wi-Fi or stays connected while websites fail. Those symptoms can point to different problems."],
    ["Compare another device at the same time", "If only one device disconnects, begin with that device’s network troubleshooting. If all do, check the router’s normal status indicators."],
    ["Check cables and power", "Look for a loose router power or network cable. Follow the manufacturer’s restart instructions if appropriate; tell anyone using the connection first. Do not factory-reset it."],
    ["Record the time and ask for help", "Save a check when the issue happens. Contact your provider if multiple devices continue dropping. This short test cannot detect outages while the page is closed."],
  ] },
  { id: "site", title: "One website won’t open", short: "A website won’t load", icon: "laptop", description: "Everything else works, except that one page.", steps: [
    ["Confirm other sites work", "Open two familiar sites. If they respond, the issue may be limited to the destination, your browser or a network policy."],
    ["Check the address and service status", "Check for a typing error and visit the service’s official status page if it has one. Do not bypass a certificate or security warning."],
    ["Try another browser", "Use another trusted browser on the same device. If that works, review the first browser’s extensions or site settings."],
    ["Ask the site or network owner", "If it still fails, contact the service. On work or school networks, ask the administrator about restrictions instead of bypassing them."],
  ] },
] as const;
export type IssueId = typeof issues[number]["id"];
