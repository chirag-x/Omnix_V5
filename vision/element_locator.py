from loguru import logger

class ElementLocator:

    def __init__(self, vision_manager):

        logger.info("Initializing Element Locator")

        self.vision_manager = vision_manager

    def _get_text_elements(self):

        frame = self.vision_manager.get_latest_frame()

        if frame is None:
            return []

        return frame.texts

    # ------------------------------------------------
    # Basic text search (improved matching)
    # ------------------------------------------------
    def find_text(self, target):

        texts = self._get_text_elements()

        target = target.lower()

        for element in texts:

            text = (element.text or "").lower()

            if target in text or text in target:

                logger.info(f"Element found: {text}")
                return element

        logger.warning(f"Element not found: {target}")
        return None

    # ------------------------------------------------
    # Return ALL elements containing text
    # ------------------------------------------------
    def find_all(self, target):

        texts = self._get_text_elements()

        target = target.lower()

        results = []

        for element in texts:

            text = (element.text or "").lower()

            if target in text or text in target:
                results.append(element)

        logger.info(f"Found {len(results)} elements for '{target}'")

        return results

    # ------------------------------------------------
    # Sort elements by vertical position
    # ------------------------------------------------
    def sort_by_position(self, elements):

        return sorted(elements, key=lambda e: e.bbox.center_y if e.bbox else 0)

    # ------------------------------------------------
    # Find nth result
    # ------------------------------------------------
    def find_nth(self, target, index):

        elements = self.find_all(target)

        if not elements:
            return None

        elements = self.sort_by_position(elements)

        if index >= len(elements):

            logger.warning("Requested index out of range")
            return None

        element = elements[index]

        logger.info(f"Selected result #{index+1}: {element.text}")

        return element

    # ------------------------------------------------
    # Return clickable coordinates
    # ------------------------------------------------
    def get_coordinates(self, element):

        if not element or not element.bbox:
            return None

        return (
            element.bbox.center_x,
            element.bbox.center_y,
        )

    # ------------------------------------------------
    # Find elements likely to be search results
    # ------------------------------------------------
    def find_ranked_results(self):

        texts = self._get_text_elements()

        if not texts:
            return []

        candidates = [t for t in texts if len(t.text or "") > 4]

        candidates = self.sort_by_position(candidates)

        logger.info(f"Detected {len(candidates)} possible results")

        return candidates

    # ------------------------------------------------
    # Get result by ranking
    # ------------------------------------------------
    def get_result(self, index):

        results = self.find_ranked_results()

        if index >= len(results):
            return None

        return results[index]

    # ------------------------------------------------
    # Detect vertical lists
    # ------------------------------------------------
    def detect_vertical_list(self):

        texts = self._get_text_elements()

        if not texts or len(texts) < 3:
            return []

        sorted_items = sorted(texts, key=lambda e: e.bbox.center_y if e.bbox else 0)

        groups = []

        for i in range(len(sorted_items) - 1):

            current = sorted_items[i]
            nxt = sorted_items[i + 1]

            dy = abs(nxt.bbox.center_y - current.bbox.center_y)

            if 10 < dy < 80:
                groups.append(current)

        if groups:
            logger.info(f"Detected list with {len(groups)} items")

        return groups

    # ------------------------------------------------
    # Find UI object near text
    # ------------------------------------------------
    def find_near_object(self, text_target, object_type, radius=120):

        frame = self.vision_manager.get_latest_frame()

        if frame is None:
            return None

        texts = frame.texts
        objects = frame.objects

        for text in texts:

            label = (text.text or "").lower()

            if text_target.lower() in label:

                tx = text.bbox.center_x
                ty = text.bbox.center_y
                for obj in objects:

                    if obj.label.lower() == object_type.lower():

                        ox = obj.bbox.center_x
                        oy = obj.bbox.center_y

                        dx = abs(ox - tx)
                        dy = abs(oy - ty)

                        if dx < radius and dy < radius:

                            logger.info(f"Found {object_type} near '{label}'")

                            return obj

        return None
