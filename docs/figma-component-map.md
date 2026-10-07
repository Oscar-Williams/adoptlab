# AdoptLab Figma and code contracts

| FigmaName | code/path |
| --- | --- |
| Button | adoptlab/static/workspace.js |
| FeedbackState | adoptlab/static/workspace.js |

The native JavaScript implementation reuses `button(label, action, primary, disabled)` and `card(title, ...content)` rather than adding a framework. Button labels map to the Label property; disabled state is derived from the run state or a pending action, and `finally` restores the exact clicked element. State presentation derives from API results and independent rules. Native DOM components are not framework AST exports; this explicit file association is not an automatically generated component import.

Design tokens are in `adoptlab/static/workspace.css`: seven shared colors and 8/16/24/32 pixel spacings. Microsoft YaHei/Segoe UI supply readable sans-serif text; Consolas supplies technical identifiers. Native Auto Layout frames define containers. Prototype navigation uses a 180 ms dissolve; the web app changes routes without motion, honoring keyboard use and avoiding animation as a prerequisite.

Figma information panels are editable design examples. The application adds live forms, actual counts, retained run selection and expanded evidence. A structural or behavioral difference must be reviewed explicitly; screenshots alone do not establish pixel parity. The local design context, motion inventory and module screenshots remain in the designated design workspace.
## Field mapping

The `Field` component set (`11:1343`) has Default, Error and Disabled variants. Its editable Label/Value properties map manually to `field(label, input)` and the native input/textarea/select elements in `adoptlab/static/workspace.js`. This is a documented semantic mapping, not an AST-generated component import. Form values and errors remain driven by the application APIs.
