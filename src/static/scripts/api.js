function qrLogin(callback) {
    let ws = new WebSocket(`ws://${window.location.host}/qrlogin`)
    console.log("Logging in...")
    ws.onmessage = (msg) => {
        let data = JSON.parse(msg.data)
        let type = data["type"]

        switch (type) {
            case "auth":
                let qr = data["img"]
                let link = data["link"]
                document.getElementById("qr").src = `data:image/png;base64, ${qr}`
                document.getElementById("qr").alt = link
                document.getElementById("qr").hidden = false
                console.log("Fetched QR-code")
                break
            case "status":
                let status = data["status"]

                if (status === "logged in") {
                    document.cookie = `session=${data["session"]};domain=${window.location.hostname}`
                    console.log("Logged in")
                    const label = document.getElementById("user-label")
                    document.getElementById("login").hidden = true
                    document.getElementById("logout").hidden = false
                    label.innerText = data["username"]
                    label.hidden = false
                    callback()
                    ws.close()
                }
                break
        }
    }
    ws.onclose = (ws) => {
        console.log("WS closed | OK ->", ws.wasClean)
    }
}

function Login(callback) {
    let ws = new WebSocket(`ws://${window.location.host}/login`)
    console.log("Logging in...")

    ws.onmessage = (msg) => {
        let data = JSON.parse(msg.data)
        let type = data["type"]
        switch (type) {
            case "status":
                let status = data["status"]

                if (status === "logged in") {
                    document.cookie = `session=${data["session"]};domain=${window.location.hostname}`
                    console.log("Logged in")
                    const label = document.getElementById("user-label")
                    document.getElementById("login").hidden = true
                    document.getElementById("logout").hidden = false
                    label.innerText = data["username"]
                    label.hidden = false
                    callback()
                    ws.close()
                }
                break
            case "f2a":
                const f2a = showF2AInput()
                f2a.oninput = () => {
                    if (f2a.value.length >= 5) {
                        f2a.disabled = true
                        ws.send(JSON.stringify({"code": f2a.value}))
                        f2a.onchange = () => {}
                    }
                }
        }
    }

    ws.onclose = (ws) => {
        console.log("WS closed | OK ->", ws.wasClean)
    }

    const phone = document.getElementById("phone-input")
    const password = document.getElementById("password-input")

    phone.disabled = true
    password.disabled = true

    ws.onopen = () => {
        ws.send(JSON.stringify({phone: phone.value, password: password.value}))
    }
}

function logout() {
    const label = document.getElementById("user-label")
    document.getElementById("login").hidden = false
    document.getElementById("logout").hidden = true
    label.innerText = ""
    label.hidden = true
    document.cookie = `session=;domain=${window.location.hostname};expires=Thu, 01 Jan 1970 00:00:01 GMT`
    fetch("/logout")
        .then((response) => {
            if (response.status === 200) {
                console.log("Logged out")
            } else {
                console.log("Error during logging out")
            }
        })
}

function start() {
    document.getElementById("graph").src = "/start"
    document.getElementById("graph").hidden = false
}