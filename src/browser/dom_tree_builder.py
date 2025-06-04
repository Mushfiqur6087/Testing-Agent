import time
import sys
import os

# Add the project root to Python path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

class DomTreeBuilder:
    def __init__(self, page, debug_mode=False):
        self.page = page
        self.debug_mode = debug_mode
        if debug_mode:
            self.perf_metrics = {
                "build_dom_tree_calls": 0,
                "timings": {
                    "build_dom_tree": 0,
                    "is_interactive_element": 0,
                    "is_element_visible": 0,
                },
                "node_metrics": {
                    "total_nodes": 0,
                    "processed_nodes": 0,
                    "skipped_nodes": 0,
                }
            }
        else:
            self.perf_metrics = None

        self._init_js_functions()

    def _init_js_functions(self):
        self.page.evaluate("""() => {
            window.domTreeHelpers = {
                isElementVisible: (element) => {
                    if (!element) return false;
                    const style = window.getComputedStyle(element);
                    return element.offsetWidth > 0 &&
                           element.offsetHeight > 0 &&
                           style.display !== 'none' &&
                           style.visibility !== 'hidden' &&
                           style.opacity !== '0';
                },

                isInteractiveElement: (element) => {
                    if (!element) return false;

                    const tagName = element.tagName.toLowerCase();

                    if (['a', 'button', 'input', 'select', 'textarea', 'details', 'audio', 'video'].includes(tagName)) {
                        return true;
                    }

                    if (element.hasAttribute('role') &&
                        ['button', 'link', 'checkbox', 'menuitem', 'menuitemcheckbox', 'menuitemradio',
                         'option', 'radio', 'searchbox', 'switch', 'tab'].includes(element.getAttribute('role'))) {
                        return true;
                    }

                    if (element.onclick || element.onmousedown || element.onmouseup ||
                        element.onkeydown || element.onkeyup) {
                        return true;
                    }

                    const style = window.getComputedStyle(element);
                    if (style.cursor === 'pointer') {
                        return true;
                    }

                    return false;
                },

                isInViewport: (element) => {
                    if (!element) return false;

                    const rect = element.getBoundingClientRect();
                    const viewportWidth = window.innerWidth;
                    const viewportHeight = window.innerHeight;

                    return (
                        rect.bottom >= 0 &&
                        rect.right >= 0 &&
                        rect.top <= viewportHeight &&
                        rect.left <= viewportWidth
                    );
                }
            };
        }""")

    def measure_time(self, fn, metric_name=None):
        if not self.debug_mode:
            return fn()

        start = time.time()
        result = fn()
        duration = (time.time() - start) * 1000

        if metric_name and metric_name in self.perf_metrics["timings"]:
            self.perf_metrics["timings"][metric_name] += duration

        return result

    def is_element_visible(self, element_handle):
        if element_handle is None:
            return False

        def check():
            try:
                return element_handle.evaluate("element => window.domTreeHelpers.isElementVisible(element)")
            except:
                return False

        return self.measure_time(check, "is_element_visible")

    def is_interactive_element(self, element_handle):
        if element_handle is None:
            return False

        def check():
            try:
                return element_handle.evaluate("element => window.domTreeHelpers.isInteractiveElement(element)")
            except:
                return False

        return self.measure_time(check, "is_interactive_element")

    def is_in_viewport(self, element_handle):
        try:
            return element_handle.evaluate("element => window.domTreeHelpers.isInViewport(element)")
        except:
            return False

    def build_dom_tree(self, element_handle=None):
        if self.debug_mode:
            self.perf_metrics["build_dom_tree_calls"] += 1

        if element_handle is None:
            element_handle = self.page.query_selector('body')

        if element_handle is None:
            return None

        start_time = time.time()
        if self.debug_mode:
            self.perf_metrics["node_metrics"]["total_nodes"] += 1

        is_visible = self.is_element_visible(element_handle)
        is_in_viewport = self.is_in_viewport(element_handle)

        if not is_visible or not is_in_viewport:
            if self.debug_mode:
                self.perf_metrics["node_metrics"]["skipped_nodes"] += 1
            return None

        if self.debug_mode:
            self.perf_metrics["node_metrics"]["processed_nodes"] += 1

        is_interactive = self.is_interactive_element(element_handle)

        tag_name = element_handle.evaluate("el => el.tagName.toLowerCase()")
        text_content = element_handle.evaluate("el => el.textContent || ''")
        inner_text = element_handle.evaluate("el => el.innerText || ''")

        attributes = element_handle.evaluate("""
            element => {
                const attrs = {};
                for (const attr of element.attributes) {
                    attrs[attr.name] = attr.value;
                }
                return attrs;
            }
        """)

        node_data = {
            "nodeName": tag_name,
            "textContent": text_content,
            "innerText": inner_text,
            "attributes": attributes,
            "children": [],
            "isInteractive": is_interactive,
            "isVisible": is_visible
        }

        child_elements = element_handle.query_selector_all(':scope > *')
        for child in child_elements:
            child_tree = self.build_dom_tree(child)
            if child_tree:
                node_data["children"].append(child_tree)

        if self.debug_mode:
            duration = (time.time() - start_time) * 1000
            self.perf_metrics["timings"]["build_dom_tree"] += duration

        return node_data

    def get_dom_tree(self):
        if self.debug_mode:
            for key in self.perf_metrics["timings"]:
                self.perf_metrics["timings"][key] = 0
            self.perf_metrics["build_dom_tree_calls"] = 0
            self.perf_metrics["node_metrics"] = {
                "total_nodes": 0,
                "processed_nodes": 0,
                "skipped_nodes": 0,
            }

        tree = self.build_dom_tree()
        result = {"tree": tree}

        if self.debug_mode:
            result["perfMetrics"] = self.perf_metrics

        return result
