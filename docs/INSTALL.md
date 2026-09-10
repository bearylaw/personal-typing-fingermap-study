# Installing ZEHN on Windows

No driver needs to be written. ZEHN is expressed as a 32-character string in exactly the
format [neo2-llkh](https://github.com/MaxGyver83/neo2-llkh) accepts, so the existing,
maintained Neo driver does all the work — including the symbol layer, which is the part
that matters most if you write code.

## 1. Get the driver

Download `neo-llkh.exe` from the neo2-llkh releases page. It is a single executable; it
does not install anything into Windows and it does not touch the registry.

## 2. Put a `settings.ini` next to it

```ini
[Settings]
customLayout=lvdwfj,oqykrstncuieahgßzmbp.üöäx
symmetricalLevel3Modifiers=1
qwertzForShortcuts=1
capsLockEnabled=0
supportLevels5and6=0
debugWindow=0
```

What those lines do, and why they are chosen:

| Setting | Effect |
|---|---|
| `customLayout` | The 32 characters, filling `q…ü` then `a…ä` then `y…-`. |
| `symmetricalLevel3Modifiers=1` | Mod3 on **both** CapsLock (left pinky) and the `ä` key (right pinky), so you can always reach a symbol with the opposite hand. This is what makes the symbol layer cheap — see [RESULTS.md](../RESULTS.md). |
| `qwertzForShortcuts=1` | **Ctrl+Z / X / C / V / A / S stay on their QWERTZ keys.** This is the setting that makes a full layout switch survivable for a developer, and it removes any reason to constrain the layout for shortcut compatibility. |
| `capsLockEnabled=0` | CapsLock becomes Mod3 instead of caps lock. You will not miss it. |

Run the exe. To start it with Windows, drop a shortcut in
`shell:startup`.

## 3. The symbol layer

Hold Mod3 (CapsLock or `ä`) and the main block becomes:

```
    …  _  [  ]  ^      !  <  >  =  &  ſ
     \  /  {  }  *      ?  (  )  -  :  @
      #  $  |  ~  `      +  %  "  '  ;
```

Use the hand *opposite* the symbol — right Mod3 for a left-hand symbol and vice versa.
`(` and `)` land on the right index and middle home keys; `{` `}` on the left middle and
index home keys; `\` on the left pinky home key. On QWERTZ those are `Shift+8`, `Shift+9`,
`AltGr+7`, `AltGr+0` and `AltGr+ß`.

## 4. Learning it

Expect three to six weeks to return to your old speed, with the first week genuinely
unpleasant. Two things make it much easier:

- **Learn the symbol layer first, on QWERTZ.** You can run neo2-llkh with
  `layout=qwertz` plus `symmetricalLevel3Modifiers=1` to get Neo's layer 3 on top of the
  letters you already know. This is where most of the benefit is if you write code, and it
  costs nothing to unlearn.
- **Keep a QWERTZ escape hatch.** Quit the exe and you are back to the system layout
  instantly, which matters when someone else uses your machine or you are on a call.

## Alternatives worth considering instead

If a 32-key relearn is not worth it to you — a defensible conclusion, see the honest
assessment in [RESULTS.md](../RESULTS.md) — the ranked fallbacks are:

1. **Neo layer 3 on top of QWERTZ.** Largest measured win per hour invested, and the
   letters do not move at all.
2. **AdNW or KOY** (`layout=adnw` / `layout=koy`). Within noise of ZEHN on every measure
   that does not come from my own effort model, and they have a community, tutorials and a
   decade of use behind them.
3. **The partial-move layouts** in the Pareto table in RESULTS.md, if you want a fraction
   of the benefit for a fraction of the retraining.
