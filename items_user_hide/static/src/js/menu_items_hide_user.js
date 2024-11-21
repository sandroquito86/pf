/** @odoo-module **/

import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { CheckBox } from "@web/core/checkbox/checkbox";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

const userMenuRegistry = registry.category("user_menuitems");

const ALLOWED_MENU_ITEMS = ["shortcuts", "settings","logout"];

export class UserMenu extends Component {
    setup() {
        this.user = useService("user");
        const { origin } = browser.location;
        const { userId } = this.user;
        this.source = `${origin}/web/image?model=res.users&field=avatar_128&id=${userId}`;
    }

    getElements() {
        const sortedItems = userMenuRegistry
            .getAll()
            .map((element) => element(this.env))
            .filter((item) => ALLOWED_MENU_ITEMS.includes(item.id))
            .sort((x, y) => {
                const xSeq = x.sequence ? x.sequence : 100;
                const ySeq = y.sequence ? y.sequence : 100;
                return xSeq - ySeq;
            });
        return sortedItems;
    }
}

UserMenu.template = "web.UserMenu";
UserMenu.components = { Dropdown, DropdownItem, CheckBox };
UserMenu.props = {};

// Registramos el nuevo componente
export const systrayItem = {
    Component: UserMenu,
};

// Forzamos el reemplazo del componente existente
registry.category("systray").add("web.user_menu", systrayItem, { sequence: 0, force: true });