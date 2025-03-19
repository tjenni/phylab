function get_current_page()
    if PANDOC_STATE and PANDOC_STATE.input_files then
        local file = PANDOC_STATE.input_files[1]
        file = file:match("([^/]+)$")
        return file:gsub("%.md$", ".html") -- .md in .html umwandeln
    end
    return nil
end

function render_navigation(nav, current_page)
    if type(nav) ~= "table" then return "" end
    local html = "<nav><ul>"
    for _, item in ipairs(nav) do
        local title = pandoc.utils.stringify(item.title)
        local link = pandoc.utils.stringify(item.url)

        link = link:gsub("%.md$", ".html")

        -- Falls der Link der aktuellen Seite entspricht, füge class="active" hinzu
        local class = (link == current_page) and ' class="active"' or ""

        html = html .. string.format('<li><a href="%s"%s>%s</a></li>', link, class, title)
    end
    html = html .. "</ul></nav>"
    return html
end

function render_breadcrumbs(breadcrumbs, current_page)
    if type(breadcrumbs) ~= "table" then return "" end
    local html = "<nav class='breadcrumbs'>"
    for i, item in ipairs(breadcrumbs) do
        local title = pandoc.utils.stringify(item.title)
        local link = pandoc.utils.stringify(item.url)

        link = link:gsub("%.md$", ".html")

        -- Falls der Link der aktuellen Seite entspricht, füge class="active" hinzu
        --local class = (link == current_page) and ' class="active"' or ""
        local class = ""

        if i > 1 then
            html = html .. " > "
        end
        html = html .. string.format('<a href="%s"%s>%s</a>', link, class, title)
    end
    html = html .. "</nav>"
    return html
end

function Meta(meta)
    local current_page = get_current_page()

    -- Breadcrumbs als MetaBlock einfügen
    if meta.breadcrumbs then
        meta.breadcrumbs_html = pandoc.MetaBlocks({ pandoc.RawBlock("html",
            render_breadcrumbs(meta.breadcrumbs, current_page)) })
    end

    -- Navigation als MetaBlock einfügen
    if meta.navigation then
        meta.navigation_html = pandoc.MetaBlocks({ pandoc.RawBlock("html",
            render_navigation(meta.navigation, current_page)) })
    end

    return meta
end

function Link(el)
    el.target = string.gsub(el.target, "%.md", ".html")
    return el
end

function Para(el)
    -- Prüfe, ob der Absatz mit `!!!` beginnt
    local text = pandoc.utils.stringify(el)

    -- Regex für `!!! note "Achtung"`
    local admonition_type, title = text:match("^!!!%s*(%w+)%s*\"(.-)\"")
    if not admonition_type then
        admonition_type = text:match("^!!!%s*(%w+)")
        title = nil
    end

    -- Falls kein `!!!` gefunden wurde, normalen Absatz zurückgeben
    if not admonition_type then
        return el
    end

    -- Inhalt nach der ersten Zeile extrahieren
    local content = {}
    for i = 2, #el.content do
        table.insert(content, el.content[i])
    end

    -- Falls kein Titel angegeben wurde, nutze den Typ als Titel
    title = title or admonition_type

    -- **HTML-Ausgabe** mit Bootstrap oder Material-Design CSS-Klassen
    if FORMAT:match("html") then
        local div = pandoc.Div(content, pandoc.Attr("", { "admonition", admonition_type }))
        table.insert(div.content, 1, pandoc.Para({ pandoc.Strong(title) }))
        return div
    end

    -- **LaTeX-Ausgabe für PDF** mit `tcolorbox`
    if FORMAT:match("latex") then
        local tex_code = "\\begin{tcolorbox}[title=" .. title .. "]\n"
        for _, block in ipairs(content) do
            tex_code = tex_code .. pandoc.write(block, "latex") .. "\n"
        end
        tex_code = tex_code .. "\\end{tcolorbox}\n"
        return pandoc.RawBlock("latex", tex_code)
    end

    -- **DOCX-Ausgabe:** Fetter Titel + eingerückter Absatz
    if FORMAT:match("docx") then
        local blocks = {}

        -- Titel fett gedruckt hinzufügen
        table.insert(blocks, pandoc.Para({ pandoc.Strong(title) }))

        -- Inhalt als BlockQuote für Hervorhebung
        for _, block in ipairs(content) do
            table.insert(blocks, pandoc.BlockQuote(block))
        end

        return blocks
    end

    -- Falls kein passendes Format gefunden wurde, normalen Absatz zurückgeben
    return el
end

function Div(el)
    -- Prüfe, ob die Klasse "solution" vorhanden ist
    if el.classes:includes("solution") then
        -- Erstelle ein <details>-Element mit <summary>
        local summary = "<details class='solution-box'>\n"
        summary = summary .. "<summary><strong>Lösung anzeigen</strong></summary>\n"

        -- Konvertiere den Inhalt des Blocks in HTML
        local content = pandoc.write(pandoc.Pandoc(el.content), "html")

        -- Erstelle das schließende </details>-Tag
        local details_end = "\n</details>"

        -- Kombiniere alles als RawBlock
        return pandoc.RawBlock("html", summary .. content .. details_end)
    end

    -- Prüfe, ob der Block mit `:::` beginnt
    if el.classes and #el.classes > 0 then
        local block_type = el.classes[1] -- Erster Klasseneintrag (info, warning, etc.)

        -- **HTML-Format**
        if FORMAT:match("html") then
            local div = pandoc.Div(el.content, pandoc.Attr("", { "admonition", block_type }))
            return div
        end

        -- **LaTeX-Format (für PDF mit tcolorbox)**
        if FORMAT:match("latex") then
            local tex_code = "\\begin{tcolorbox}[title=" .. block_type .. "]\n"
            for _, block in ipairs(el.content) do
                tex_code = tex_code .. pandoc.write(block, "latex") .. "\n"
            end
            tex_code = tex_code .. "\\end{tcolorbox}\n"
            return pandoc.RawBlock("latex", tex_code)
        end

        -- **DOCX-Format**
        if FORMAT:match("docx") then
            local blocks = {}
            -- Titel fett als erste Zeile
            table.insert(blocks, pandoc.Para({ pandoc.Strong(block_type) }))

            -- Inhalt als Absatz mit Einrückung
            for _, block in ipairs(el.content) do
                if block.t == "Para" then
                    table.insert(blocks, pandoc.BlockQuote(block))
                else
                    table.insert(blocks, block)
                end
            end

            return blocks
        end
    end

    -- Falls keine `:::`-Syntax, dann unverändert zurückgeben
    return el
end
