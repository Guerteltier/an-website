// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0-or-later
(() => {
    let bigIntType = "bigint";
    try {
        BigInt(69);
    } catch (e) {
        // fix for cool browsers like Pale Moon that don't support BigInt
        // eslint-disable-next-line no-global-assign
        BigInt = Number as unknown as BigIntConstructor;
        bigIntType = "number";
    }
    const output = elById("output") as HTMLInputElement;

    const fields: [
        HTMLInputElement,
        HTMLInputElement,
        HTMLInputElement,
        HTMLInputElement,
    ] = [
        elById("euro") as HTMLInputElement, // Euro
        elById("mark") as HTMLInputElement, // Deutsche Mark
        elById("ost") as HTMLInputElement, // Ostmark
        elById("schwarz") as HTMLInputElement, // Ostmark auf dem Schwarzmarkt
    ];
    const factors: [
        bigint | number,
        bigint | number,
        bigint | number,
        bigint | number,
    ] = [
        BigInt(1), // Euro
        BigInt(2), // Deutsche Mark
        BigInt(4), // Ostmark
        BigInt(20), // Ostmark auf dem Schwarzmarkt
    ];
    const numberRegex = /^(?:\d+|(?:\d+)?[,.]\d{1,2}|\d+[,.](?:\d{1,2})?)?$/;

    const isZero = (str: string) => /^0*$/.test(str);

    function getDisplayValue(wert: string | bigint | number): null | string {
        if (typeof wert === "string") {
            wert = strToBigInt(wert);
        }

        if (typeof wert !== bigIntType) {
            alert(`Ungültiger Wert ${wert} mit type ${typeof wert}`);
            return null;
        }

        if (typeof wert === "number") {
            wert = Math.floor(wert);
        }

        let str = wert.toString();
        if (bigIntType === "number" && str.includes("e")) {
            const [num, pow] = str.split("e");

            if (pow.startsWith("-")) {
                return "0"; // too small to be displayed
            }

            // eslint-disable-next-line prefer-const
            let [int, dec] = num.split(".");
            dec = dec || "";
            str = int + dec + "0".repeat(parseInt(pow) - dec.length);
        }
        if (isZero(str)) {
            return "0"; // is empty string or 0
        }

        const dec = str.slice(-2); // last two chars or whole str if len <= 2
        return (
            (str.slice(0, -2) || "0") + // integer part, but "0" instead of ""
            (
                isZero(dec)
                    ? "" // if is integer do not append
                    : "," + (dec.length === 1 ? "0" : "") + dec
            )
        );
    }

    function strToBigInt(str: string): number | bigint {
        if (isZero(str)) {
            return BigInt(0);
        }

        let [int, dec] = [str, "00"];
        if (str.includes(",")) {
            [int, dec] = str.split(",");
        } else if (str.includes(".")) {
            [int, dec] = str.split(".");
        }
        if (dec.length !== 2) {
            // get the first two digits after the comma, fill with 0 if needed
            dec = (dec + "00").slice(0, 2);
        }
        return BigInt(int + dec);
    }

    PopStateHandlers["currencyConverter"] = (e: PopStateEvent) =>
        setAllFields(
            strToBigInt((e.state as { euro: string })["euro"].toString()),
        );

    const setEuroParam = (euroVal: string, push: boolean) =>
        setURLParam(
            "euro",
            euroVal,
            { euro: euroVal },
            "currencyConverter",
            push,
        );

    function setAllFields(
        euroValue: bigint | number,
        ignored: number | null = null,
    ) {
        setEuroParam(getDisplayValue(euroValue) || "null", false);
        for (let i = 0; i < 4; i++) {
            const value = getDisplayValue(
                (euroValue as bigint) * (factors[i] as bigint),
            );
            fields[i].placeholder = value || "null";
            if (i !== ignored) {
                fields[i].value = value || "null";
            }
        }
    }

    const updateOutput = () => {
        // deno-fmt-ignore
        output.value = fields[0].value + " Euro, das sind ja " +
            fields[1].value + " Mark; " +
            fields[2].value + " Ostmark und " +
            fields[3].value + " Ostmark auf dem Schwarzmarkt!";
    };

    function onSubmit(event: Event) {
        event.preventDefault();
        for (const field of fields) {
            field.value = getDisplayValue(field.value) || "null";
        }
        setEuroParam(fields[0].value, true);
        updateOutput();
    }

    for (let i = 0; i < 4; i++) {
        fields[i].oninput = () => {
            // remove "invalid" class
            for (const field of fields) {
                field.className = "";
            }
            // add "invalid" class if input is not a number
            if (!numberRegex.test(fields[i].value)) {
                fields[i].className = "invalid";
                return;
            }
            // parse input as it is a number
            setAllFields(
                (strToBigInt(fields[i].value) as bigint) /
                    (factors[i] as bigint),
                i,
            );

            updateOutput();
        };
    }
    // set the value of the fields to the placeholder set by tornado
    for (const field of fields) {
        field.value = field.placeholder;
    }
    // fix form submit
    (elById("form") as HTMLFormElement).onsubmit = onSubmit;
})();
// @license-end
