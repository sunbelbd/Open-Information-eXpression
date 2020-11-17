"""
Visualizer for graph
"""
import io

import os

def dot2image(dot_string, file_name=None, return_img=False):
    """

    @param g:
    @param file_name:
    @return:
    """

    from PIL import Image

    import tempfile
    dot_file = tempfile.NamedTemporaryFile(mode='w', suffix=".dot", delete=False)
    dot_file.write(dot_string)
    dot_file.close()

    if not file_name and return_img:
        import tempfile
        fout = tempfile.NamedTemporaryFile(suffix=".png")
        file_name = fout.name

    os.system("dot -T png {0} -o {1}".format(dot_file.name, file_name))

    if return_img:
        return Image.open(file_name)




def make_square(im, size=1024, fill_color=(255, 255, 255, 255)):
    from PIL import Image
    x, y = im.size
    temp_size = max(size, x, y)
    new_im = Image.new('RGBA', (temp_size, temp_size), fill_color)
    new_im.paste(im, (int((temp_size - x) / 2), int((temp_size - y) / 2)))
    if temp_size != size:
        new_im = new_im.resize((size, size))
    return new_im


def add_title(image, title, height):
    """

    @param image:
    @type image:
    @return:
    @rtype:
    """


    # import required classes

    from PIL import Image, ImageDraw, ImageFont

    # create Image object with the input image

    image = Image.open('background.png')

    # initialise the drawing context with
    # the image object as background

    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype('Roboto-Bold.ttf', size=45)

    # starting position of the message

    (x, y) = (50, 50)
    message = "Happy Birthday!"
    color = 'rgb(0, 0, 0)'  # black color

    # draw the message on the background

    draw.text((x, y), message, fill=color, font=font)
    (x, y) = (150, 150)
    name = 'Vinay'
    color = 'rgb(255, 255, 255)'  # white color
    draw.text((x, y), name, fill=color, font=font)

    # save the edited image

    image.save('greeting_card.png')

def concat_images(images):
    """

    @param images:
    @type images:
    @return:
    @rtype:
    """

    import sys
    from PIL import Image

    widths, heights = zip(*(i.size for i in images))

    total_width = sum(widths)
    max_height = max(heights)

    new_im = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset, 0))
        x_offset += im.size[0]

    return new_im


def make_pair_image(image1, image2):
    """

    @param ctb_image:
    @param oia_image:
    @return:
    """

    image1 = make_square(image1, size=1024)
    image2 = make_square(image2, size=1024)

    new_im = concat_images([image1, image2])

    return new_im


import os

def make_video(images, output_video_path,  size, fps=5,
               is_color=True, format="XVID"):



    import cv2
    import numpy
    import os

    each_image_duration = fps  # in secs
    fourcc = cv2.VideoWriter_fourcc(*format)  # define the video codec

    video = cv2.VideoWriter(output_video_path, fourcc, 1.0, size, is_color )

    for image in images:
        for _ in range(each_image_duration):
            cv_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)

            video.write(cv_image)

    video.release()

    cv2.destroyAllWindows()





class GraphVisualizer(object):

    """
    BasicGraphVisualizer
    """


    def node_label(self, graph, node, *args, **kwargs):
        """

        :param node:
        :type node:
        :return:
        :rtype:
        """


        return str(node)

    def node_style(self, graph, node, *args, **kwargs):
        """

        @param graph:
        @param node:
        @param args:
        @param kwargs:
        @return:
        """
        return {}

    def edge_label(self, graph, edge, *args, **kwargs):
        """

        :param edge:
        :type edge:
        :return:
        :rtype:
        """
        return str(edge)

    def edge_style(self, graph, edge,  *args, **kwargs):
        """

        @param graph:
        @param edge:
        @param args:
        @param kwargs:
        @return:
        """

        return {}


    def visualize(self, graph, file_name=None, return_img=False, *args, **kwargs):
        """

        @return:
        @rtype:
        """

        dot_string = io.StringIO()

        dot_string.write("strict digraph {\n")

        node2index = dict()
        for index, node_id in enumerate(graph.g.nodes()):
            node = graph.get_node(node_id)

            node_label = self.node_label(graph, node, *args, **kwargs)
            node_style = self.node_style(graph, node, *args, **kwargs)
            node2index[node.ID] = index

            node_attr = ['label="{0}"'.format(node_label)]
            for k, v in node_style.items():
                node_attr.append('{0}="{1}"'.format(k, v))

            vis_node_label = '{0}\t[{1}]; \n'.format(
                index, ", ".join(node_attr)
            )

            dot_string.write(vis_node_label)
            # if simple:
            #     g.add_node(id2index[node_id], label=node_text, shape=shape)
            # else:
            #     g.add_node(node_id, label=node_text, shape=shape)

        for s, e in graph.g.edges():
            edge = graph.g[s][e]["Edge"]

            edge_label = self.edge_label(graph, edge, *args, **kwargs)
            edge_style = self.edge_style(graph, edge, *args, **kwargs)

            edge_attr = ['label="{0}"'.format(edge_label)]
            for k, v in edge_style.items():
                edge_attr.append('{0}="{1}"'.format(k, v))

            s = node2index[s]
            e = node2index[e]

            dot_string.write('{0}\t->\t{1}\t[{2}];\n'.format(
                s, e, ", ".join(edge_attr)
            ))

        dot_string.write("}\n")

        dot_string = dot_string.getvalue()

        result = dot_string

        if file_name or return_img:

            image = dot2image(dot_string, file_name, return_img)

        if return_img:
            result = image

        return result
